import json
from typing import List
from pydantic import BaseModel, Field
from agents.base import BaseCivicAgent
from models.schemas import CentralDecisionOutput, DispatchedAgencyTicket, ExecutiveDecisionInsight, GeoJurisdictionOutput, MitosKnowledgeOutput, SmartSLAContextOutput, ValidationCriticOutput, VisionTriageOutput


class DecisionSynthesisLLMOutput(BaseModel):
    citizen_unified_message_el: str = Field(..., description="Ενοποιημένο μήνυμα πολίτη")
    apps_saved_count: int = Field(..., description="Αριθμός εφαρμογών που γλίτωσε ο πολίτης")
    executive_insight: ExecutiveDecisionInsight


DECISION_SYSTEM_INSTRUCTION = """Είσαι ο Agent 6 (CentralDecisionAgent). Σύνθεση απόφασης και Decision Support.""".strip()


class CentralDecisionAgent(BaseCivicAgent):
    def __init__(self) -> None:
        super().__init__(6, "central_decision_agent", "Agent 6: Central Decision Support")

    async def synthesize_decision(self, vision_output: VisionTriageOutput, geo_output: GeoJurisdictionOutput, sla_output: SmartSLAContextOutput, mitos_output: MitosKnowledgeOutput, validation_output: ValidationCriticOutput, dispatched_tickets: List[DispatchedAgencyTicket], total_duration_ms: int) -> CentralDecisionOutput:
        prompt = f"""Tickets: {len(dispatched_tickets)}"""
        llm_out = await self.generate_structured(prompt, DecisionSynthesisLLMOutput, DECISION_SYSTEM_INSTRUCTION, temperature=0.2)
        return CentralDecisionOutput(
            citizen_unified_message_el=llm_out.citizen_unified_message_el,
            apps_saved_count=llm_out.apps_saved_count,
            dispatched_tickets=dispatched_tickets,
            executive_insight=llm_out.executive_insight,
            total_pipeline_duration_ms=total_duration_ms,
        )
