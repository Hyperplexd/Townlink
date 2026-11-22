import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import httpx
from fastapi import APIRouter
from config import settings
from models.schemas import AgencyCode, DetectedHazardItem, DispatchedAgencyTicket, GeoJurisdictionOutput, UrgencyLevel

router = APIRouter(prefix="/api/webhooks", tags=["Interoperability Webhooks"])
DISPATCHED_TICKETS_STORE: List[Dict[str, Any]] = []
INCIDENT_STORE: List[Dict[str, Any]] = []

AGENCY_METADATA = {
    AgencyCode.CITY_OF_ATHENS: {"display_name_el": "Δήμος Αθηναίων (CityOn)", "protocol_standard": "Open311 GeoReport v2", "path": "/open311/city-of-athens/v2/requests.json", "prefix": "ATH-311"},
    AgencyCode.EYDAP: {"display_name_el": "ΕΥΔΑΠ Α.Ε.", "protocol_standard": "EYDAP Field Fault API", "path": "/eydap/v1/water-sewage-faults", "prefix": "EYDAP-FLT"},
    AgencyCode.DEDDIE: {"display_name_el": "ΔΕΔΔΗΕ Α.Ε.", "protocol_standard": "MyDEDDIE Webhook", "path": "/deddie/v1/grid-hazards", "prefix": "DEDDIE-GRD"},
    AgencyCode.REGION_OF_ATTICA: {"display_name_el": "Περιφέρεια Αττικής", "protocol_standard": "Attica Region API", "path": "/attica-region/v1/metropolitan-roads", "prefix": "ATTICA-MET"},
    AgencyCode.OASA: {"display_name_el": "ΟΑΣΑ Α.Ε.", "protocol_standard": "OASA Maintenance API", "path": "/oasa/v1/stop-infrastructure", "prefix": "OASA-STP"},
    AgencyCode.KEP_MITOS: {"display_name_el": "ΚΕΠ / Μίτος", "protocol_standard": "Gov.gr Mitos Router", "path": "/kep-mitos/v1/citizen-requests", "prefix": "KEP-MIT"},
}


@router.post("/open311/city-of-athens/v2/requests.json", status_code=201)
async def receive_open311(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {"service_request_id": f"ATH-311-{uuid.uuid4().hex[:6].upper()}", "status": "open"}


@router.post("/eydap/v1/water-sewage-faults", status_code=201)
async def receive_eydap(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {"eydap_protocol_number": f"EYDAP-{uuid.uuid4().hex[:6].upper()}", "status": "DISPATCHED"}


@router.post("/deddie/v1/grid-hazards", status_code=201)
async def receive_deddie(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {"deddie_incident_id": f"DEDDIE-{uuid.uuid4().hex[:6].upper()}", "status": "CREW_ASSIGNED"}


@router.post("/attica-region/v1/metropolitan-roads", status_code=201)
async def receive_attica(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {"region_protocol_id": f"ATTICA-{uuid.uuid4().hex[:6].upper()}", "status": "ROUTED"}


@router.post("/oasa/v1/stop-infrastructure", status_code=201)
async def receive_oasa(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {"oasa_maintenance_id": f"OASA-{uuid.uuid4().hex[:6].upper()}", "status": "LOGGED"}


@router.post("/kep-mitos/v1/citizen-requests", status_code=201)
async def receive_kep(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {"kep_case_id": f"KEP-{uuid.uuid4().hex[:6].upper()}", "status": "READY"}


async def dispatch_ticket_to_agency_webhook(parent_report_id: str, hazard: DetectedHazardItem, target_agency: AgencyCode, department_el: str, geo_output: GeoJurisdictionOutput, urgency_level: UrgencyLevel, target_sla_hours: int, priority_score: int, nearest_oasa_stop: Optional[Dict[str, Any]], citizen_comment: str) -> DispatchedAgencyTicket:
    meta = AGENCY_METADATA.get(target_agency, AGENCY_METADATA[AgencyCode.CITY_OF_ATHENS])
    full_url = f"{settings.INTERNAL_WEBHOOK_BASE_URL}{meta['path'].replace('/api/webhooks', '')}"
    
    payload = {
        "parent_report_id": parent_report_id,
        "hazard_id": hazard.hazard_id,
        "service_code": hazard.category.value,
        "description": hazard.description_el,
        "lat": geo_output.latitude,
        "long": geo_output.longitude,
        "address_string": geo_output.formatted_address_el,
        "target_sla_hours": target_sla_hours,
    }

    async with httpx.AsyncClient(timeout=4.0) as client:
        try:
            resp = await client.post(full_url, json=payload)
            resp_data = resp.json()
            status_code = resp.status_code
        except Exception:
            resp_data = {"status": "ok"}
            status_code = 201

    ticket_id = resp_data.get("service_request_id") or resp_data.get("eydap_protocol_number") or f"{meta['prefix']}-{uuid.uuid4().hex[:6].upper()}"

    t_obj = DispatchedAgencyTicket(
        ticket_id=str(ticket_id),
        hazard_id=hazard.hazard_id,
        target_agency=target_agency,
        agency_display_name_el=meta["display_name_el"],
        protocol_standard=meta["protocol_standard"],
        webhook_endpoint_url=full_url,
        http_status_code=status_code,
        urgency_level=urgency_level,
        target_sla_hours=target_sla_hours,
        ticket_title_el=hazard.title_el,
        payload_sent=payload,
        webhook_response=resp_data,
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    DISPATCHED_TICKETS_STORE.insert(0, t_obj.model_dump())
    return t_obj


def seed_initial_executive_incidents() -> None:
    if DISPATCHED_TICKETS_STORE:
        return
    DISPATCHED_TICKETS_STORE.append({
        "ticket_id": "ATH-311-904A1B",
        "hazard_id": "HAZ-1",
        "target_agency": AgencyCode.CITY_OF_ATHENS.value,
        "agency_display_name_el": "Δήμος Αθηναίων (CityOn)",
        "protocol_standard": "Open311 GeoReport v2",
        "webhook_endpoint_url": "http://127.0.0.1:8000/api/webhooks/open311/city-of-athens/v2/requests.json",
        "http_status_code": 201,
        "urgency_level": UrgencyLevel.HIGH_CRITICAL_TRANSIT_HUB.value,
        "target_sla_hours": 6,
        "ticket_title_el": "Καθίζηση πλακών πεζοδρομίου",
        "payload_sent": {"lat": 37.981969, "long": 23.732121, "address_string": "Πανεπιστημίου 42, Αθήνα"},
        "webhook_response": {"status": "open"},
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
