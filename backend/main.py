import json
import truststore
from datetime import datetime, timezone
from typing import Any, Dict, Optional

# Avast/AVG HTTPS scanning re-signs TLS with a root that lives in the Windows
# store. httpx only trusts certifi, so Gemini calls fail unless we use the OS store.
truststore.inject_into_ssl()
from fastapi import FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse
from config import active_llm_api_key, bind_request_llm_keys, reasoning_model_name, settings, vision_model_name, active_llm_provider
from agents.orchestrator import orchestrator
from demo_assets import get_demo_presets_with_images, get_preset_image_bytes
from webhooks.agency_endpoints import DISPATCHED_TICKETS_STORE, INCIDENT_STORE, router as webhooks_router, seed_initial_executive_incidents

app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(webhooks_router)


@app.on_event("startup")
async def startup_event() -> None:
    seed_initial_executive_incidents()


@app.get("/api/health")
async def health_check() -> Dict[str, Any]:
    provider = active_llm_provider()
    return {
        "status": "ok",
        "llm_provider": provider,
        "llm_api_key_configured": provider is not None,
        "gemini_api_key_configured": bool(settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.strip()),
        "openrouter_api_key_configured": bool(settings.OPENROUTER_API_KEY and settings.OPENROUTER_API_KEY.strip()),
        "vision_model": vision_model_name() if provider else None,
        "reasoning_model": reasoning_model_name() if provider else None,
    }


@app.get("/api/presets")
async def list_presets() -> Dict[str, Any]:
    return {"presets": get_demo_presets_with_images()}


@app.post("/api/incidents/stream")
async def stream_incident(
    citizen_comment: str = Form(""),
    latitude: float = Form(37.981969),
    longitude: float = Form(23.732121),
    preset_id: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    x_gemini_api_key: Optional[str] = Header(None),
    x_openrouter_api_key: Optional[str] = Header(None),
    x_llm_api_key: Optional[str] = Header(None),
) -> EventSourceResponse:
    try:
        bind_request_llm_keys(x_gemini_api_key, x_openrouter_api_key, x_llm_api_key)
    except ValueError:
        raise HTTPException(status_code=400, detail="Λείπει κλειδί μοντέλου. Βάλε τιμή στο GEMINI_API_KEY ή στο OPENROUTER_API_KEY.")
    key = active_llm_api_key()

    img_bytes = await image.read() if image else (get_preset_image_bytes(preset_id) if preset_id else None)

    async def event_generator():
        async for ev in orchestrator.run_pipeline_stream(citizen_comment, latitude, longitude, img_bytes, api_key=key):
            if ev["event"] == "pipeline_complete":
                INCIDENT_STORE.insert(0, ev["data"])
            yield {"event": ev["event"], "data": json.dumps(ev["data"], ensure_ascii=False)}

    return EventSourceResponse(event_generator())


def _is_critical_sla(ticket: Dict[str, Any]) -> bool:
    sla = ticket.get("target_sla_hours")
    urgency = str(ticket.get("urgency_level") or "")
    if isinstance(sla, (int, float)) and sla <= 8:
        return True
    return urgency in {"HIGH_CRITICAL_TRANSIT_HUB", "CRITICAL_SAFETY_HAZARD"}


@app.get("/api/executive/dashboard")
async def executive_dashboard() -> Dict[str, Any]:
    agency_counts: Dict[str, int] = {}
    comm_counts: Dict[str, int] = {}
    for ticket in DISPATCHED_TICKETS_STORE:
        agency = ticket.get("target_agency", "CITY_OF_ATHENS")
        agency_counts[agency] = agency_counts.get(agency, 0) + 1
    for report in INCIDENT_STORE:
        name = ((report.get("geo_output") or {}).get("municipal_community_name_el") or "").strip()
        if not name:
            continue
        comm_counts[name] = comm_counts.get(name, 0) + 1

    return {
        "total_dispatched_tickets": len(DISPATCHED_TICKETS_STORE),
        "critical_sla_count": sum(1 for ticket in DISPATCHED_TICKETS_STORE if _is_critical_sla(ticket)),
        "agency_breakdown": agency_counts,
        "community_breakdown": comm_counts,
        "tickets": DISPATCHED_TICKETS_STORE,
        "recent_reports": INCIDENT_STORE[:10],
    }


class ExecutiveBriefingOutput(BaseModel):
    headline_summary_el: str = Field(..., description="Συνοπτική εικόνα")
    cross_agency_clusters_el: list[str] = Field(..., description="Συσχετίσεις")
    priority_dispatch_recommendations_el: list[str] = Field(..., description="Προτάσεις")
    estimated_efficiency_gain_pct: int = Field(..., ge=15, le=85)


@app.post("/api/executive/ai-briefing")
async def executive_briefing(
    x_gemini_api_key: Optional[str] = Header(None),
    x_openrouter_api_key: Optional[str] = Header(None),
    x_llm_api_key: Optional[str] = Header(None),
) -> Dict[str, Any]:
    try:
        bind_request_llm_keys(x_gemini_api_key, x_openrouter_api_key, x_llm_api_key)
    except ValueError:
        raise HTTPException(status_code=400, detail="Απαιτείται GEMINI_API_KEY ή OPENROUTER_API_KEY.")
    key = active_llm_api_key()
    orchestrator.decision_agent.set_api_key(key)
    prompt = f"Ανάλυσε τα tickets: {json.dumps(DISPATCHED_TICKETS_STORE[:5])}"
    res = await orchestrator.decision_agent.generate_structured(prompt, ExecutiveBriefingOutput, "Σμβουλος Δήμου", temperature=0.2)
    return res.model_dump()
