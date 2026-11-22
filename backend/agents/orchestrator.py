import asyncio
import base64
import time
import uuid
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Dict, List, Optional
from agents.vision_agent import VisionTriageAgent
from agents.geo_agent import GeoJurisdictionAgent
from agents.sla_agent import SmartSLAContextAgent
from agents.mitos_agent import MitosKnowledgeAgent
from agents.validation_agent import ValidationCriticAgent
from agents.decision_agent import CentralDecisionAgent
from models.schemas import AgentStepTrace, CompleteIncidentReport, DispatchedAgencyTicket
from config import active_llm_provider, reasoning_model_name, vision_model_name
from webhooks.agency_endpoints import dispatch_ticket_to_agency_webhook


class TownLinkOrchestrator:
    def __init__(self) -> None:
        self.vision_agent = VisionTriageAgent()
        self.geo_agent = GeoJurisdictionAgent()
        self.sla_agent = SmartSLAContextAgent()
        self.mitos_agent = MitosKnowledgeAgent()
        self.validation_agent = ValidationCriticAgent()
        self.decision_agent = CentralDecisionAgent()

    def _set_api_key_if_provided(self, api_key: Optional[str]) -> None:
        if api_key:
            for a in (self.vision_agent, self.geo_agent, self.sla_agent, self.mitos_agent, self.validation_agent, self.decision_agent):
                a.set_api_key(api_key)

    async def run_pipeline_stream(self, citizen_comment: str, lat: float, lon: float, image_bytes: Optional[bytes] = None, image_mime_type: str = "image/jpeg", api_key: Optional[str] = None) -> AsyncGenerator[Dict[str, Any], None]:
        self._set_api_key_if_provided(api_key)
        start_t = time.perf_counter()
        report_id = f"ATH-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        traces: List[AgentStepTrace] = []

        image_data_url = f"data:{image_mime_type};base64,{base64.b64encode(image_bytes).decode('utf-8')}" if image_bytes else None

        # Step 1
        yield {"event": "agent_start", "data": {"agent_number": 1, "agent_id": self.vision_agent.agent_id, "agent_name_el": self.vision_agent.agent_name_el, "message_el": "Vision AI Triage..."}}
        t0 = time.perf_counter()
        vision_output = await self.vision_agent.analyze(citizen_comment, image_bytes, image_mime_type)
        t1 = int((time.perf_counter() - t0) * 1000)
        tr1 = AgentStepTrace(agent_number=1, agent_id=self.vision_agent.agent_id, agent_name_el=self.vision_agent.agent_name_el, status="completed", duration_ms=t1, summary_el=f"Εντοπίστηκαν {len(vision_output.detected_hazards)} βλάβες.", api_calls_made=[_llm_trace("vision")], structured_output=vision_output.model_dump())
        traces.append(tr1)
        yield {"event": "agent_complete", "data": tr1.model_dump()}

        # Step 2
        yield {"event": "agent_start", "data": {"agent_number": 2, "agent_id": self.geo_agent.agent_id, "agent_name_el": self.geo_agent.agent_name_el, "message_el": "GIS & Jurisdiction Resolver..."}}
        t0 = time.perf_counter()
        geo_output, live_geo = await self.geo_agent.resolve_jurisdiction(lat, lon, vision_output)
        t2 = int((time.perf_counter() - t0) * 1000)
        tr2 = AgentStepTrace(agent_number=2, agent_id=self.geo_agent.agent_id, agent_name_el=self.geo_agent.agent_name_el, status="completed", duration_ms=t2, summary_el=geo_output.formatted_address_el, api_calls_made=["OSM Nominatim", "Athens GIS"], structured_output=geo_output.model_dump())
        traces.append(tr2)
        yield {"event": "agent_complete", "data": tr2.model_dump()}

        # Steps 3 & 4
        yield {"event": "agent_start", "data": {"agent_number": 3, "agent_id": self.sla_agent.agent_id, "agent_name_el": self.sla_agent.agent_name_el, "message_el": "OASA Telematics & Smart SLA..."}}
        yield {"event": "agent_start", "data": {"agent_number": 4, "agent_id": self.mitos_agent.agent_id, "agent_name_el": self.mitos_agent.agent_name_el, "message_el": "Mitos Procedures API..."}}
        t0 = time.perf_counter()
        sla_output, _ = await self.sla_agent.evaluate_sla(lat, lon, vision_output, geo_output, live_geo)
        mitos_output, _ = await self.mitos_agent.retrieve_procedures(citizen_comment, vision_output, geo_output)
        t34 = int((time.perf_counter() - t0) * 1000)

        tr3 = AgentStepTrace(agent_number=3, agent_id=self.sla_agent.agent_id, agent_name_el=self.sla_agent.agent_name_el, status="completed", duration_ms=t34, summary_el=f"Urgency: {sla_output.overall_urgency.value}", api_calls_made=["OASA API"], structured_output=sla_output.model_dump())
        traces.append(tr3)
        yield {"event": "agent_complete", "data": tr3.model_dump()}

        tr4 = AgentStepTrace(agent_number=4, agent_id=self.mitos_agent.agent_id, agent_name_el=self.mitos_agent.agent_name_el, status="completed", duration_ms=t34, summary_el=f"{len(mitos_output.matched_procedures)} procedures", api_calls_made=["Mitos API"], structured_output=mitos_output.model_dump())
        traces.append(tr4)
        yield {"event": "agent_complete", "data": tr4.model_dump()}

        # Step 5
        yield {"event": "agent_start", "data": {"agent_number": 5, "agent_id": self.validation_agent.agent_id, "agent_name_el": self.validation_agent.agent_name_el, "message_el": "Validation Critic Guardrail..."}}
        t0 = time.perf_counter()
        val_output = await self.validation_agent.validate_pipeline(citizen_comment, vision_output, geo_output, sla_output, mitos_output)
        t5 = int((time.perf_counter() - t0) * 1000)
        tr5 = AgentStepTrace(agent_number=5, agent_id=self.validation_agent.agent_id, agent_name_el=self.validation_agent.agent_name_el, status="completed", duration_ms=t5, summary_el=f"Trust Score: {int(val_output.overall_trust_score * 100)}%", api_calls_made=[_llm_trace("reasoning")], structured_output=val_output.model_dump())
        traces.append(tr5)
        yield {"event": "agent_complete", "data": tr5.model_dump()}

        # Step 6
        yield {"event": "agent_start", "data": {"agent_number": 6, "agent_id": self.decision_agent.agent_id, "agent_name_el": self.decision_agent.agent_name_el, "message_el": "Central Decision Support & Webhook Dispatch..."}}
        t0 = time.perf_counter()
        dispatched = []
        for hazard in vision_output.detected_hazards:
            jurisdiction = next((m for m in geo_output.jurisdiction_mappings if m.hazard_id == hazard.hazard_id), None)
            target_agency = jurisdiction.final_agency if jurisdiction else hazard.preliminary_agency
            ticket = await dispatch_ticket_to_agency_webhook(report_id, hazard, target_agency, "Υπηρεσία", geo_output, sla_output.overall_urgency, 24, 85, None, citizen_comment)
            dispatched.append(ticket)

        total_ms = int((time.perf_counter() - start_t) * 1000)
        decision_output = await self.decision_agent.synthesize_decision(vision_output, geo_output, sla_output, mitos_output, val_output, dispatched, total_ms)
        t6 = int((time.perf_counter() - t0) * 1000)

        tr6 = AgentStepTrace(agent_number=6, agent_id=self.decision_agent.agent_id, agent_name_el=self.decision_agent.agent_name_el, status="completed", duration_ms=t6, summary_el=f"Dispatched {len(dispatched)} tickets.", api_calls_made=["Live Agency Webhooks"], structured_output=decision_output.model_dump())
        traces.append(tr6)
        yield {"event": "agent_complete", "data": tr6.model_dump()}

        report = CompleteIncidentReport(
            report_id=report_id,
            created_at=datetime.now(timezone.utc).isoformat(),
            citizen_comment=citizen_comment,
            latitude=lat,
            longitude=lon,
            image_data_url=image_data_url,
            vision_output=vision_output,
            geo_output=geo_output,
            sla_output=sla_output,
            mitos_output=mitos_output,
            validation_output=val_output,
            decision_output=decision_output,
            agent_traces=traces,
        )
        yield {"event": "pipeline_complete", "data": report.model_dump()}


def _llm_trace(role: str) -> str:
    provider = "OpenRouter" if active_llm_provider() == "openrouter" else "Gemini"
    model = vision_model_name() if role == "vision" else reasoning_model_name()
    return f"{provider} {model}"


orchestrator = TownLinkOrchestrator()
