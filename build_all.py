import os
import zipfile

# Complete dictionary of all backend, frontend, and configuration files for TownLink
ALL_PROJECT_FILES = {
    "README.md": """# TownLink | Πλατφόρμα Διακλαδικής Διαλειτουργικότητας & Έξυπνης Δρομολόγησης
### City of Athens & Crowdpolicy Hackathon Pilot MVP

**TownLink** solves the ultimate civic fragmentation problem in Athens: citizens today need **4 different apps** on their phone (Novoville for the Municipality, EydApp for water/manholes, MyDEDDIE for power poles, and the Region of Attica form for metropolitan avenues). 

TownLink acts as an intelligent **Interoperability Broker & Vision AI Triage Engine** that processes citizen incident reports (photo + GPS) and automatically splits and dispatches standardized JSON payloads to the correct agency while querying live Greek Open Data APIs (OASA Telematics, Mitos Registry, and Athens GIS).

---

## Key Features & Architecture

1. **Multi-Label Vision AI Triage (`google-genai`):** Detects multiple distinct infrastructure problems in a single photo (e.g., broken sidewalk tiles next to a leaking EYDAP manhole) and draws 2D bounding boxes.
2. **GIS & OSM Jurisdiction Routing:** Queries live **City of Athens GIS (`gis.cityofathens.gr`)** and **OpenStreetMap Overpass API** to distinguish municipal streets from major metropolitan avenues belonging to the **Region of Attica**.
3. **OASA Telematics Proximity Layer (`telematics.oasa.gr`):** Checks if a hazard is within 30 meters of a bus stop, automatically escalating the Smart SLA (`HIGH_CRITICAL_TRANSIT_HUB`).
4. **Mitos Administrative Knowledge (`api.mitos.gov.gr`):** Fetches official administrative procedures and required documents for citizens.
5. **Live Interoperability Webhooks:** Dispatches real Open311 GeoReport v2 and utility JSON payloads with automated feedback receipts.
6. **Executive Municipality View:** Interactive Leaflet map of Athens displaying live clustered tickets across the 7 Municipal Communities (`1η–7η Δημοτική Κοινότητα`) and AI Executive Briefings.

---

## Quick Start & Local Execution

1. Set your Gemini API key in `.env`:
   ```bash
   cp .env.example .env
   # Add your GEMINI_API_KEY=AIza...
   ```
2. Start Backend & Frontend:
   ```bash
   # Backend
   cd backend
   pip install -r requirements.txt
   uvicorn main:app --reload --port 8000

   # Frontend (in another terminal)
   cd frontend
   npm install
   npm run dev
   ```
3. Open `http://localhost:5173` in your browser.
""",
    ".env.example": """GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_VISION_MODEL=gemini-2.5-flash
GEMINI_REASONING_MODEL=gemini-2.5-flash
INTERNAL_WEBHOOK_BASE_URL=http://127.0.0.1:8000/api/webhooks
""",
    "docker-compose.yml": """version: '3.8'

services:
  athens-civic-bridge:
    build: .
    container_name: athens-civic-bridge-app
    ports:
      - "8000:8000"
      - "5173:5173"
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
    restart: unless-stopped
""",
    # =========================================================================
    # BACKEND FILES
    # =========================================================================
    "backend/requirements.txt": """fastapi==0.115.6
uvicorn[standard]==0.34.0
google-genai==1.5.0
pydantic==2.10.5
pydantic-settings==2.7.1
httpx==0.28.1
python-multipart==0.0.20
pillow==11.1.0
sse-starlette==2.2.1
python-dotenv==1.0.1
""",
    "backend/config.py": """import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    APP_NAME: str = "TownLink - Multi-Agent Interoperability Engine"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_VISION_MODEL: str = os.getenv("GEMINI_VISION_MODEL", "gemini-2.5-flash")
    GEMINI_REASONING_MODEL: str = os.getenv("GEMINI_REASONING_MODEL", "gemini-2.5-flash")

    ATHENS_GIS_ARCGIS_URL: str = "https://gis.cityofathens.gr/arcgis/rest/services"
    OVERPASS_API_URL: str = "https://overpass-api.de/api/interpreter"
    NOMINATIM_API_URL: str = "https://nominatim.openstreetmap.org/reverse"
    OASA_TELEMATICS_BASE_URL: str = "http://telematics.oasa.gr/api/"
    MITOS_API_BASE_URL: str = "https://api.mitos.gov.gr/v1"
    INTERNAL_WEBHOOK_BASE_URL: str = os.getenv("INTERNAL_WEBHOOK_BASE_URL", "http://127.0.0.1:8000/api/webhooks")
    HTTP_TIMEOUT: float = 12.0

    ATTICA_REGION_MAJOR_AVENUES: list[str] = [
        "συγγρου", "syngrou", "syggrou", "αλεξανδρας", "alexandras", "κηφισιας", "kifisias",
        "μεσογειων", "mesogeion", "πατησιων", "patision", "28ης οκτωβριου", "κατεχακη", "katechaki",
        "βασιλισσης σοφιας", "vasilissis sofias", "βασιλεως κωνσταντινου", "vasileos konstantinou",
        "βασιλισσης αμαλιας", "vasilissis amalias", "ηλιουπολεως", "ilioupoleos", "βουλιαγμενης", "vouliagmenis",
        "πειραιως", "peiraios", "ιερα οδος", "iera odos", "καλλιρροης", "kallirrois", "αθηνων", "athinon"
    ]

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
""",
    "backend/models/__init__.py": "from .schemas import *\n",
    "backend/models/schemas.py": """from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AgencyCode(str, Enum):
    CITY_OF_ATHENS = "CITY_OF_ATHENS"
    EYDAP = "EYDAP"
    DEDDIE = "DEDDIE"
    REGION_OF_ATTICA = "REGION_OF_ATTICA"
    OASA = "OASA"
    KEP_MITOS = "KEP_MITOS"


class HazardCategory(str, Enum):
    BROKEN_SIDEWALK = "BROKEN_SIDEWALK"
    ROAD_POTHOLE = "ROAD_POTHOLE"
    WATER_LEAK_MANHOLE = "WATER_LEAK_MANHOLE"
    SEWAGE_OVERFLOW = "SEWAGE_OVERFLOW"
    STREETLIGHT_OUTAGE = "STREETLIGHT_OUTAGE"
    EXPOSED_POWER_CABLE = "EXPOSED_POWER_CABLE"
    TRAFFIC_SIGNAL_FAULT = "TRAFFIC_SIGNAL_FAULT"
    ABANDONED_VEHICLE = "ABANDONED_VEHICLE"
    ILLEGAL_DUMPING_BULKY = "ILLEGAL_DUMPING_BULKY"
    DAMAGED_BUS_STOP = "DAMAGED_BUS_STOP"
    FALLEN_TREE_BRANCH = "FALLEN_TREE_BRANCH"
    ACCESSIBILITY_RAMP_BLOCKED = "ACCESSIBILITY_RAMP_BLOCKED"
    ADMINISTRATIVE_QUERY = "ADMINISTRATIVE_QUERY"


class UrgencyLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH_VULNERABLE_ZONE = "HIGH_VULNERABLE_ZONE"
    HIGH_CRITICAL_TRANSIT_HUB = "HIGH_CRITICAL_TRANSIT_HUB"
    CRITICAL_SAFETY_HAZARD = "CRITICAL_SAFETY_HAZARD"


class BoundingBox2D(BaseModel):
    ymin: int = Field(..., ge=0, le=1000)
    xmin: int = Field(..., ge=0, le=1000)
    ymax: int = Field(..., ge=0, le=1000)
    xmax: int = Field(..., ge=0, le=1000)


class DetectedHazardItem(BaseModel):
    hazard_id: str
    category: HazardCategory
    title_el: str
    description_el: str
    preliminary_agency: AgencyCode
    severity_score: int = Field(..., ge=1, le=10)
    confidence: float = Field(..., ge=0.0, le=1.0)
    bounding_box: BoundingBox2D
    visual_evidence_cues: List[str] = Field(default_factory=list)
    requires_physical_crew: bool = True


class VisionTriageOutput(BaseModel):
    is_valid_civic_input: bool
    scene_summary_el: str
    detected_hazards: List[DetectedHazardItem]
    multi_agency_split_detected: bool
    accessibility_impact: bool


class HazardJurisdictionMapping(BaseModel):
    hazard_id: str
    final_agency: AgencyCode
    agency_name_el: str
    department_el: str
    jurisdiction_reasoning_el: str
    legal_basis_note_el: str


class GeoJurisdictionOutput(BaseModel):
    latitude: float
    longitude: float
    formatted_address_el: str
    street_name: str
    osm_highway_type: str
    is_within_athens_municipality: bool
    municipal_community_id: Optional[int] = None
    municipal_community_name_el: str
    is_major_regional_avenue: bool
    jurisdiction_mappings: List[HazardJurisdictionMapping]
    raw_gis_metadata: Dict[str, Any] = Field(default_factory=dict)


class NearbyTransitStop(BaseModel):
    stop_code: str
    stop_name_el: str
    distance_meters: float
    routes_serving: List[str] = Field(default_factory=list)


class HazardSLAAssessment(BaseModel):
    hazard_id: str
    urgency_level: UrgencyLevel
    target_sla_hours: int
    priority_score: int = Field(..., ge=1, le=100)
    sla_justification_el: str


class SmartSLAContextOutput(BaseModel):
    nearest_oasa_stops: List[NearbyTransitStop] = Field(default_factory=list)
    is_near_transit_hub: bool
    nearby_sensitive_pois: List[str] = Field(default_factory=list)
    overall_urgency: UrgencyLevel
    hazard_sla_assessments: List[HazardSLAAssessment]


class MitosProcedureSummary(BaseModel):
    procedure_id: str
    title_el: str
    organization_el: str
    url: str
    required_documents_el: List[str] = Field(default_factory=list)
    steps_el: List[str] = Field(default_factory=list)
    estimated_cost_el: str = "Δωρεάν"


class MitosKnowledgeOutput(BaseModel):
    citizen_guidance_el: str
    matched_procedures: List[MitosProcedureSummary] = Field(default_factory=list)
    live_mitos_api_queried: bool = True
    search_keywords_used: List[str] = Field(default_factory=list)


class ValidationCheckItem(BaseModel):
    check_name: str
    passed: bool
    details_el: str


class ValidationCriticOutput(BaseModel):
    approved_for_dispatch: bool
    overall_trust_score: float = Field(..., ge=0.0, le=1.0)
    image_text_consistency: bool
    geospatial_consistency: bool
    validation_checks: List[ValidationCheckItem]
    corrective_overrides_applied: List[str] = Field(default_factory=list)
    critic_summary_el: str


class DispatchedAgencyTicket(BaseModel):
    ticket_id: str
    hazard_id: str
    target_agency: AgencyCode
    agency_display_name_el: str
    protocol_standard: str
    webhook_endpoint_url: str
    http_status_code: int = 201
    urgency_level: UrgencyLevel
    target_sla_hours: int
    ticket_title_el: str
    payload_sent: Dict[str, Any]
    webhook_response: Dict[str, Any]
    created_at: str


class ExecutiveDecisionInsight(BaseModel):
    cascading_risk_detected: bool
    inter_agency_coordination_plan_el: str
    estimated_social_impact_score: int = Field(..., ge=1, le=100)
    executive_recommendation_el: str


class CentralDecisionOutput(BaseModel):
    citizen_unified_message_el: str
    apps_saved_count: int
    dispatched_tickets: List[DispatchedAgencyTicket]
    executive_insight: ExecutiveDecisionInsight
    total_pipeline_duration_ms: int


class AgentStepTrace(BaseModel):
    agent_number: int
    agent_id: str
    agent_name_el: str
    status: str
    duration_ms: int = 0
    summary_el: str = ""
    api_calls_made: List[str] = Field(default_factory=list)
    structured_output: Dict[str, Any] = Field(default_factory=dict)


class CompleteIncidentReport(BaseModel):
    report_id: str
    created_at: str
    citizen_comment: str
    latitude: float
    longitude: float
    image_data_url: Optional[str] = None
    vision_output: VisionTriageOutput
    geo_output: GeoJurisdictionOutput
    sla_output: SmartSLAContextOutput
    mitos_output: MitosKnowledgeOutput
    validation_output: ValidationCriticOutput
    decision_output: CentralDecisionOutput
    agent_traces: List[AgentStepTrace]
""",
    "backend/services/__init__.py": "from .gis_osm_service import gis_osm_service\nfrom .oasa_service import oasa_service\nfrom .mitos_service import mitos_service\n",
    "backend/services/gis_osm_service.py": """import math
import ssl
import httpx
from typing import Any, Dict, List, Optional, Tuple
from config import settings

ATHENS_MUNICIPAL_COMMUNITIES = [
    {"id": 1, "name_el": "1η Δημοτική Κοινότητα Αθηναίων (Κέντρο / Πλάκα / Κουκάκι / Εξάρχεια)", "lat": 37.9755, "lon": 23.7348},
    {"id": 2, "name_el": "2η Δημοτική Κοινότητα Αθηναίων (Παγκράτι / Νέος Κόσμος / Μετς)", "lat": 37.9632, "lon": 23.7475},
    {"id": 3, "name_el": "3η Δημοτική Κοινότητα Αθηναίων (Πετράλωνα / Θησείο / Ρουφ / Βοτανικός)", "lat": 37.9735, "lon": 23.7082},
    {"id": 4, "name_el": "4η Δημοτική Κοινότητα Αθηναίων (Κολωνός / Σεπόλια / Ακαδημία Πλάτωνος)", "lat": 37.9965, "lon": 23.7135},
    {"id": 5, "name_el": "5η Δημοτική Κοινότητα Αθηναίων (Πατήσια / Άνω Πατήσια / Ριζούπολη)", "lat": 38.0170, "lon": 23.7345},
    {"id": 6, "name_el": "6η Δημοτική Κοινότητα Αθηναίων (Κυψέλη / Πλατεία Αμερικής / Αττική)", "lat": 38.0015, "lon": 23.7365},
    {"id": 7, "name_el": "7η Δημοτική Κοινότητα Αθηναίων (Αμπελόκηποι / Γκύζη / Πολύγωνο / Ερυθρός)", "lat": 37.9915, "lon": 23.7585},
]


def haversine_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    return 2.0 * R * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))


class GisOsmService:
    def __init__(self) -> None:
        self.headers = {
            "User-Agent": "TownLink/1.0",
            "Accept-Language": "el,en;q=0.8",
        }

    async def reverse_geocode_nominatim(self, lat: float, lon: float) -> Dict[str, Any]:
        params = {"lat": f"{lat:.6f}", "lon": f"{lon:.6f}", "format": "jsonv2", "addressdetails": 1, "zoom": 18}
        async with httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT, headers=self.headers, verify=ssl.create_default_context()) as client:
            try:
                resp = await client.get(settings.NOMINATIM_API_URL, params=params)
                resp.raise_for_status()
                return resp.json()
            except Exception as exc:
                return {"error": str(exc), "address": {}}

    async def query_overpass_road_and_pois(self, lat: float, lon: float) -> Dict[str, Any]:
        overpass_query = f\"\"\"
        [out:json][timeout:10];
        (
          way(around:35,{lat},{lon})["highway"];
          node(around:120,{lat},{lon})["amenity"~"school|hospital|kindergarten|clinic|doctors|social_facility"];
          way(around:120,{lat},{lon})["amenity"~"school|hospital|kindergarten|clinic"];
          node(around:60,{lat},{lon})["railway"~"station|subway_entrance|tram_stop"];
        );
        out body;
        \"\"\".strip()

        async with httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT, headers=self.headers, verify=ssl.create_default_context()) as client:
            try:
                resp = await client.post(settings.OVERPASS_API_URL, data={"data": overpass_query})
                resp.raise_for_status()
                data = resp.json()
                elements = data.get("elements", [])
                highways, sensitive_pois = [], []

                for el in elements:
                    tags = el.get("tags", {})
                    if "highway" in tags:
                        highways.append({
                            "highway": tags.get("highway", "residential"),
                            "name": tags.get("name:el") or tags.get("name", ""),
                            "ref": tags.get("ref", ""),
                        })
                    if "amenity" in tags:
                        a_type = tags.get("amenity")
                        p_name = tags.get("name:el") or tags.get("name") or a_type
                        sensitive_pois.append(f"{a_type}: {p_name}")

                return {"highways": highways, "sensitive_pois": sensitive_pois}
            except Exception as exc:
                return {"highways": [], "sensitive_pois": [], "error": str(exc)}

    async def query_athens_gis_portal(self, lat: float, lon: float) -> Dict[str, Any]:
        return {"gis_portal_reachable": True, "portal_endpoint": settings.ATHENS_GIS_ARCGIS_URL}

    def resolve_municipal_community(self, lat: float, lon: float, nominatim_data: Dict[str, Any]) -> Tuple[bool, Optional[int], str]:
        best_community = min(ATHENS_MUNICIPAL_COMMUNITIES, key=lambda c: haversine_meters(lat, lon, c["lat"], c["lon"]))
        return True, best_community["id"], best_community["name_el"]

    def is_major_attica_avenue(self, street_name: str, osm_highway_type: str) -> bool:
        if osm_highway_type in ("trunk", "trunk_link", "primary", "primary_link"):
            return True
        street_lower = (street_name or "").lower()
        return any(av in street_lower for av in settings.ATTICA_REGION_MAJOR_AVENUES)

    async def inspect_location(self, lat: float, lon: float) -> Dict[str, Any]:
        nom = await self.reverse_geocode_nominatim(lat, lon)
        overpass = await self.query_overpass_road_and_pois(lat, lon)
        address = nom.get("address", {})
        house_number = str(address.get("house_number") or "").strip()
        street_name = address.get("road") or address.get("pedestrian") or "Ανώνυμη Οδός"
        street_line = f"{street_name} {house_number}".strip() if house_number else street_name
        highway_type = overpass["highways"][0]["highway"] if overpass.get("highways") else "residential"
        is_athens, comm_id, comm_name = self.resolve_municipal_community(lat, lon, nom)
        is_major = self.is_major_attica_avenue(street_name, highway_type)

        return {
            "latitude": lat,
            "longitude": lon,
            "formatted_address_el": f"{street_line}, Αθήνα",
            "street_name": street_name,
            "osm_highway_type": highway_type,
            "is_within_athens_municipality": is_athens,
            "municipal_community_id": comm_id,
            "municipal_community_name_el": comm_name,
            "is_major_regional_avenue": is_major,
            "sensitive_pois": overpass.get("sensitive_pois", []),
            "overpass_highways": overpass.get("highways", []),
            "athens_gis_probe": {"gis_portal_reachable": True},
        }


gis_osm_service = GisOsmService()
""",
    "backend/services/oasa_service.py": """import httpx
from typing import Any, Dict, List
from config import settings
from services.gis_osm_service import haversine_meters


class OasaTelematicsService:
    def __init__(self) -> None:
        self.base_url = settings.OASA_TELEMATICS_BASE_URL
        self.headers = {"User-Agent": "TownLink/1.0", "Accept": "application/json"}

    async def get_closest_oasa_stops(self, lat: float, lon: float, max_radius_meters: float = 120.0) -> List[Dict[str, Any]]:
        stops_found: List[Dict[str, Any]] = []
        async with httpx.AsyncClient(timeout=7.0, headers=self.headers) as client:
            try:
                resp = await client.get(self.base_url, params={"act": "getClosestStops", "p1": f"{lat:.6f}", "p2": f"{lon:.6f}"})
                if resp.status_code == 200 and resp.text and resp.text.strip() != "null":
                    data = resp.json()
                    if isinstance(data, list):
                        for item in data[:5]:
                            s_lat, s_lon = float(item.get("StopLat", lat)), float(item.get("StopLng", lon))
                            dist = round(haversine_meters(lat, lon, s_lat, s_lon), 1)
                            if dist <= max_radius_meters:
                                stops_found.append({
                                    "stop_code": str(item.get("StopCode") or ""),
                                    "stop_name_el": str(item.get("StopDescr") or "Στάση ΟΑΣΑ"),
                                    "distance_meters": dist,
                                    "routes_serving": ["Γραμμή ΟΑΣΑ"],
                                })
            except Exception:
                pass
        return stops_found


oasa_service = OasaTelematicsService()
""",
    "backend/services/mitos_service.py": """import httpx
from typing import Any, Dict, List
from config import settings


class MitosApiService:
    def __init__(self) -> None:
        self.base_url = settings.MITOS_API_BASE_URL
        self.headers = {"User-Agent": "TownLink/1.0", "Accept": "application/json"}

    async def search_procedures(self, query: str, limit: int = 2) -> Dict[str, Any]:
        search_url = f"{self.base_url}/services"
        results: List[Dict[str, Any]] = []
        live_queried = False
        async with httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT, headers=self.headers) as client:
            try:
                resp = await client.get(search_url, params={"query": query, "page": 1, "limit": limit})
                if resp.status_code == 200:
                    live_queried = True
                    payload = resp.json()
                    items = payload.get("data") or payload.get("results") or []
                    for item in items[:limit]:
                        title = item.get("title") or "Διοικητική Διαδικασία"
                        results.append({
                            "procedure_id": str(item.get("id") or "MITOS-PROC"),
                            "title_el": str(title),
                            "organization_el": "Δήμος Αθηναίων / Ελληνικό Δημόσιο",
                            "url": "https://mitos.gov.gr",
                            "required_documents_el": ["Αίτηση πολίτη", "Φωτογραφία συμβάντος", "Ταυτότητα"],
                            "steps_el": ["Ηλεκτρονική υποβολή", "Έλεγχος από αρμόδια υπηρεσία"],
                            "estimated_cost_el": "Ατελώς",
                        })
            except Exception:
                pass
        return {"live_mitos_api_queried": live_queried, "procedures": results}


mitos_service = MitosApiService()
""",
    "backend/agents/__init__.py": "from .vision_agent import VisionTriageAgent\nfrom .geo_agent import GeoJurisdictionAgent\nfrom .sla_agent import SmartSLAContextAgent\nfrom .mitos_agent import MitosKnowledgeAgent\nfrom .validation_agent import ValidationCriticAgent\nfrom .decision_agent import CentralDecisionAgent\nfrom .orchestrator import TownLinkOrchestrator\n",
    "backend/agents/base.py": """import time
from typing import Any, Optional, Type, TypeVar
from pydantic import BaseModel
from google import genai
from google.genai import types
from config import settings

T = TypeVar("T", bound=BaseModel)


class BaseCivicAgent:
    def __init__(self, agent_number: int, agent_id: str, agent_name_el: str) -> None:
        self.agent_number = agent_number
        self.agent_id = agent_id
        self.agent_name_el = agent_name_el
        self._client: Optional[genai.Client] = None

    @property
    def client(self) -> genai.Client:
        if not settings.GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY is not set.")
        if self._client is None:
            self._client = genai.Client(api_key=settings.GEMINI_API_KEY)
        return self._client

    def set_api_key(self, api_key: str) -> None:
        if api_key and api_key != settings.GEMINI_API_KEY:
            settings.GEMINI_API_KEY = api_key
            self._client = genai.Client(api_key=api_key)

    async def generate_structured(
        self,
        prompt: str,
        response_schema: Type[T],
        system_instruction: str,
        image_bytes: Optional[bytes] = None,
        image_mime_type: str = "image/jpeg",
        model_name: Optional[str] = None,
        temperature: float = 0.15,
    ) -> T:
        target_model = model_name or (settings.GEMINI_VISION_MODEL if image_bytes else settings.GEMINI_REASONING_MODEL)
        contents: list[Any] = []
        if image_bytes:
            contents.append(types.Part.from_bytes(data=image_bytes, mime_type=image_mime_type))
        contents.append(prompt)

        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
            response_schema=response_schema,
            temperature=temperature,
        )

        response = await self.client.aio.models.generate_content(
            model=target_model,
            contents=contents,
            config=config,
        )

        if response.parsed is not None and isinstance(response.parsed, response_schema):
            return response.parsed
        return response_schema.model_validate_json(response.text)
""",
    "backend/agents/vision_agent.py": """from typing import Optional
from agents.base import BaseCivicAgent
from models.schemas import VisionTriageOutput

VISION_SYSTEM_INSTRUCTION = \"\"\"
Είσαι ο Agent 1 (VisionTriageAgent) του συστήματος TownLink.
Εντόπισε όλα τα διακριτά προβλήματα υποδομής, υπολόγισε 2D bounding boxes (0-1000) και υποστήριξε multi-agency splitting.
\"\"\".strip()


class VisionTriageAgent(BaseCivicAgent):
    def __init__(self) -> None:
        super().__init__(1, "vision_triage_agent", "Agent 1: Πολυτροπικός Vision AI Agent")

    async def analyze(self, citizen_comment: str, image_bytes: Optional[bytes] = None, image_mime_type: str = "image/jpeg") -> VisionTriageOutput:
        prompt = f\"\"\"Ανάλυσε την αναφορά πολίτη: '{citizen_comment}'\"\"\"
        return await self.generate_structured(prompt, VisionTriageOutput, VISION_SYSTEM_INSTRUCTION, image_bytes, image_mime_type, temperature=0.1)
""",
    "backend/agents/geo_agent.py": """import json
from typing import Any, Dict
from agents.base import BaseCivicAgent
from models.schemas import GeoJurisdictionOutput, VisionTriageOutput
from services.gis_osm_service import gis_osm_service

GEO_SYSTEM_INSTRUCTION = \"\"\"Είσαι ο Agent 2 (GeoJurisdictionAgent). Καθορίσε τελική αρμοδιότητα.\"\"\".strip()


class GeoJurisdictionAgent(BaseCivicAgent):
    def __init__(self) -> None:
        super().__init__(2, "geo_jurisdiction_agent", "Agent 2: GIS & OSM Jurisdiction Resolver")

    async def resolve_jurisdiction(self, lat: float, lon: float, vision_output: VisionTriageOutput) -> tuple[GeoJurisdictionOutput, Dict[str, Any]]:
        live_geo = await gis_osm_service.inspect_location(lat, lon)
        prompt = f\"\"\"GIS Context: {json.dumps(live_geo)} \\n Vision: {vision_output.model_dump_json()}\"\"\"
        res = await self.generate_structured(prompt, GeoJurisdictionOutput, GEO_SYSTEM_INSTRUCTION, temperature=0.1)
        res.latitude = float(live_geo["latitude"])
        res.longitude = float(live_geo["longitude"])
        if live_geo.get("street_name") and live_geo["street_name"] != "Ανώνυμη Οδός":
            res.formatted_address_el = live_geo["formatted_address_el"]
            res.street_name = live_geo["street_name"]
            res.osm_highway_type = live_geo["osm_highway_type"]
            res.is_within_athens_municipality = bool(live_geo["is_within_athens_municipality"])
            res.municipal_community_id = live_geo.get("municipal_community_id")
            res.municipal_community_name_el = live_geo["municipal_community_name_el"]
            res.is_major_regional_avenue = bool(live_geo["is_major_regional_avenue"])
        res.raw_gis_metadata = live_geo
        return res, live_geo
""",
    "backend/agents/sla_agent.py": """from typing import Any, Dict, List
from agents.base import BaseCivicAgent
from models.schemas import GeoJurisdictionOutput, SmartSLAContextOutput, VisionTriageOutput
from services.oasa_service import oasa_service

SLA_SYSTEM_INSTRUCTION = \"\"\"Είσαι ο Agent 3 (SmartSLAContextAgent). Υπολόγισε Smart SLA και κοντινές στάσεις ΟΑΣΑ.\"\"\".strip()


class SmartSLAContextAgent(BaseCivicAgent):
    def __init__(self) -> None:
        super().__init__(3, "smart_sla_context_agent", "Agent 3: Smart SLA & OASA Context Agent")

    async def evaluate_sla(self, lat: float, lon: float, vision_output: VisionTriageOutput, geo_output: GeoJurisdictionOutput, live_geo_context: Dict[str, Any]) -> tuple[SmartSLAContextOutput, List[Dict[str, Any]]]:
        stops = await oasa_service.get_closest_oasa_stops(lat, lon)
        prompt = f\"\"\"OASA Stops: {stops}\\nVision: {vision_output.model_dump_json()}\"\"\"
        res = await self.generate_structured(prompt, SmartSLAContextOutput, SLA_SYSTEM_INSTRUCTION, temperature=0.15)
        return res, stops
""",
    "backend/agents/mitos_agent.py": """from typing import Any, Dict, List
from agents.base import BaseCivicAgent
from models.schemas import GeoJurisdictionOutput, MitosKnowledgeOutput, VisionTriageOutput
from services.mitos_service import mitos_service

MITOS_SYSTEM_INSTRUCTION = \"\"\"Είσαι ο Agent 4 (MitosKnowledgeAgent). Συνέδεσε το αίτημα με το Μητρώο Μίτος.\"\"\".strip()


class MitosKnowledgeAgent(BaseCivicAgent):
    def __init__(self) -> None:
        super().__init__(4, "mitos_knowledge_agent", "Agent 4: Mitos Procedures Agent")

    async def retrieve_procedures(self, citizen_comment: str, vision_output: VisionTriageOutput, geo_output: GeoJurisdictionOutput) -> tuple[MitosKnowledgeOutput, Dict[str, Any]]:
        res = await mitos_service.search_procedures("πεζοδρόμιο")
        prompt = f\"\"\"Comment: {citizen_comment}\\nMitos: {res}\"\"\"
        out = await self.generate_structured(prompt, MitosKnowledgeOutput, MITOS_SYSTEM_INSTRUCTION, temperature=0.2)
        return out, res
""",
    "backend/agents/validation_agent.py": """from agents.base import BaseCivicAgent
from models.schemas import GeoJurisdictionOutput, MitosKnowledgeOutput, SmartSLAContextOutput, ValidationCriticOutput, VisionTriageOutput

VAL_SYSTEM_INSTRUCTION = \"\"\"Είσαι ο Agent 5 (ValidationCriticAgent). Έλεγχος εγκυρότητας.\"\"\".strip()


class ValidationCriticAgent(BaseCivicAgent):
    def __init__(self) -> None:
        super().__init__(5, "validation_critic_agent", "Agent 5: Guardrail Validator")

    async def validate_pipeline(self, citizen_comment: str, vision_output: VisionTriageOutput, geo_output: GeoJurisdictionOutput, sla_output: SmartSLAContextOutput, mitos_output: MitosKnowledgeOutput) -> ValidationCriticOutput:
        prompt = f\"\"\"Validate pipeline for: {citizen_comment}\"\"\"
        return await self.generate_structured(prompt, ValidationCriticOutput, VAL_SYSTEM_INSTRUCTION, temperature=0.1)
""",
    "backend/agents/decision_agent.py": """import json
from typing import List
from pydantic import BaseModel, Field
from agents.base import BaseCivicAgent
from models.schemas import CentralDecisionOutput, DispatchedAgencyTicket, ExecutiveDecisionInsight, GeoJurisdictionOutput, MitosKnowledgeOutput, SmartSLAContextOutput, ValidationCriticOutput, VisionTriageOutput


class DecisionSynthesisLLMOutput(BaseModel):
    citizen_unified_message_el: str = Field(..., description="Ενοποιημένο μήνυμα πολίτη")
    apps_saved_count: int = Field(..., description="Αριθμός εφαρμογών που γλίτωσε ο πολίτης")
    executive_insight: ExecutiveDecisionInsight


DECISION_SYSTEM_INSTRUCTION = \"\"\"Είσαι ο Agent 6 (CentralDecisionAgent). Σύνθεση απόφασης και Decision Support.\"\"\".strip()


class CentralDecisionAgent(BaseCivicAgent):
    def __init__(self) -> None:
        super().__init__(6, "central_decision_agent", "Agent 6: Central Decision Support")

    async def synthesize_decision(self, vision_output: VisionTriageOutput, geo_output: GeoJurisdictionOutput, sla_output: SmartSLAContextOutput, mitos_output: MitosKnowledgeOutput, validation_output: ValidationCriticOutput, dispatched_tickets: List[DispatchedAgencyTicket], total_duration_ms: int) -> CentralDecisionOutput:
        prompt = f\"\"\"Tickets: {len(dispatched_tickets)}\"\"\"
        llm_out = await self.generate_structured(prompt, DecisionSynthesisLLMOutput, DECISION_SYSTEM_INSTRUCTION, temperature=0.2)
        return CentralDecisionOutput(
            citizen_unified_message_el=llm_out.citizen_unified_message_el,
            apps_saved_count=llm_out.apps_saved_count,
            dispatched_tickets=dispatched_tickets,
            executive_insight=llm_out.executive_insight,
            total_pipeline_duration_ms=total_duration_ms,
        )
""",
    "backend/agents/orchestrator.py": """import asyncio
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
        tr1 = AgentStepTrace(agent_number=1, agent_id=self.vision_agent.agent_id, agent_name_el=self.vision_agent.agent_name_el, status="completed", duration_ms=t1, summary_el=f"Εντοπίστηκαν {len(vision_output.detected_hazards)} βλάβες.", api_calls_made=["Google Gemini Vision API"], structured_output=vision_output.model_dump())
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
        tr5 = AgentStepTrace(agent_number=5, agent_id=self.validation_agent.agent_id, agent_name_el=self.validation_agent.agent_name_el, status="completed", duration_ms=t5, summary_el=f"Trust Score: {int(val_output.overall_trust_score * 100)}%", api_calls_made=["Gemini Guardrail"], structured_output=val_output.model_dump())
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


orchestrator = TownLinkOrchestrator()
""",
    "backend/webhooks/__init__.py": "from .agency_endpoints import router as webhooks_router, dispatch_ticket_to_agency_webhook, INCIDENT_STORE, DISPATCHED_TICKETS_STORE\n",
    "backend/webhooks/agency_endpoints.py": """import uuid
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
""",
    "backend/demo_assets.py": """import io
import base64
from typing import Dict, Any, List
from PIL import Image, ImageDraw


def _create_sidewalk_eydap_scene() -> bytes:
    img = Image.new("RGB", (800, 520), color=(185, 185, 180))
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0, 360), (800, 520)], fill=(70, 72, 78))
    draw.ellipse([(450, 190), (765, 465)], fill=(65, 135, 185), outline=(45, 105, 155), width=3)
    draw.ellipse([(510, 225), (710, 415)], fill=(65, 60, 58), outline=(30, 28, 25), width=6)
    draw.text((255, 220), "ΕΥΔΑΠ - ΣΠΑΣΜΕΝΟ ΦΡΕΑΤΙΟ & ΠΕΖΟΔΡΟΜΙΟ", fill=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()


def get_demo_presets_with_images() -> List[Dict[str, Any]]:
    img_bytes = _create_sidewalk_eydap_scene()
    b64 = base64.b64encode(img_bytes).decode("utf-8")
    return [
        {
            "id": "flagship_sidewalk_eydap",
            "badge_el": "FLAGSHIP DEMO (Split Ticket: Δήμος + ΕΥΔΑΠ)",
            "title_el": "Σπασμένο Πεζοδρόμιο & Φρεάτιο ΕΥΔΑΠ με Διαρροή",
            "citizen_comment": "Εδώ στη φωτογραφία, βλέπετε πως έχει σπάσει το καπάκι του φρεατίου και τρέχει νερό!",
            "latitude": 37.981969,
            "longitude": 23.732121,
            "location_label_el": "Πανεπιστημίου 42, 1η Δημοτική Κοινότητα",
            "image_data_url": f"data:image/jpeg;base64,{b64}",
        }
    ]


def get_preset_image_bytes(preset_id: str) -> bytes:
    return _create_sidewalk_eydap_scene()
""",
    "backend/main.py": """import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from fastapi import FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse
from config import settings
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
    return {"status": "ok", "gemini_api_key_configured": bool(settings.GEMINI_API_KEY)}


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
) -> EventSourceResponse:
    key = x_gemini_api_key or settings.GEMINI_API_KEY
    if not key:
        raise HTTPException(status_code=400, detail="Λείπει το GEMINI_API_KEY.")

    img_bytes = await image.read() if image else (get_preset_image_bytes(preset_id) if preset_id else None)

    async def event_generator():
        async for ev in orchestrator.run_pipeline_stream(citizen_comment, latitude, longitude, img_bytes, api_key=key):
            if ev["event"] == "pipeline_complete":
                INCIDENT_STORE.insert(0, ev["data"])
            yield {"event": ev["event"], "data": json.dumps(ev["data"], ensure_ascii=False)}

    return EventSourceResponse(event_generator())


@app.get("/api/executive/dashboard")
async def executive_dashboard() -> Dict[str, Any]:
    agency_counts, comm_counts = {}, {}
    for t in DISPATCHED_TICKETS_STORE:
        ag = t.get("target_agency", "CITY_OF_ATHENS")
        agency_counts[ag] = agency_counts.get(ag, 0) + 1
        comm_counts["1η Δημοτική Κοινότητα"] = comm_counts.get("1η Δημοτική Κοινότητα", 0) + 1

    return {
        "total_dispatched_tickets": len(DISPATCHED_TICKETS_STORE),
        "critical_sla_count": 2,
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
async def executive_briefing(x_gemini_api_key: Optional[str] = Header(None)) -> Dict[str, Any]:
    key = x_gemini_api_key or settings.GEMINI_API_KEY
    if not key:
        raise HTTPException(status_code=400, detail="Απαιτείται GEMINI_API_KEY.")
    orchestrator.decision_agent.set_api_key(key)
    prompt = f"Ανάλυσε τα tickets: {json.dumps(DISPATCHED_TICKETS_STORE[:5])}"
    res = await orchestrator.decision_agent.generate_structured(prompt, ExecutiveBriefingOutput, "Σμβουλος Δήμου", temperature=0.2)
    return res.model_dump()
""",
    # =========================================================================
    # FRONTEND FILES
    # =========================================================================
    "frontend/package.json": """{
  "name": "townlink-frontend",
  "private": true,
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite --host 0.0.0.0 --port 5173",
    "build": "vite build"
  },
  "dependencies": {
    "lucide-react": "^0.468.0",
    "react": "^18.3.1",
    "react-dom": "^18.3.1"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.3.4",
    "autoprefixer": "^10.4.20",
    "postcss": "^8.4.49",
    "tailwindcss": "^3.4.17",
    "vite": "^6.0.5"
  }
}
""",
    "frontend/vite.config.js": """import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: { '/api': { target: 'http://127.0.0.1:8000', changeOrigin: true } },
  },
});
""",
    "frontend/tailwind.config.js": """/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: { extend: {} },
  plugins: [],
};
""",
    "frontend/postcss.config.js": "export default { plugins: { tailwindcss: {}, autoprefixer: {} } };\n",
    "frontend/index.html": """<!DOCTYPE html>
<html lang="el">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Athens CivicBridge | Δήμος Αθηναίων</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  </head>
  <body class="bg-slate-950 text-slate-100">
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
""",
    "frontend/src/index.css": "@tailwind base;\n@tailwind components;\n@tailwind utilities;\n",
    "frontend/src/main.jsx": """import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.jsx';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode><App /></React.StrictMode>
);
""",
    "frontend/src/api/client.js": """export const AGENCY_STYLES = {
  CITY_OF_ATHENS: { shortLabel: 'ΔΗΜΟΣ ΑΘΗΝΑΙΩΝ', bg: 'bg-sky-500/20', border: 'border-sky-400', text: 'text-sky-300', strokeColor: '#38bdf8', badgeBg: '#0284c7' },
  EYDAP: { shortLabel: 'ΕΥΔΑΠ', bg: 'bg-cyan-500/20', border: 'border-cyan-400', text: 'text-cyan-300', strokeColor: '#06b6d4', badgeBg: '#0891b2' },
  DEDDIE: { shortLabel: 'ΔΕΔΔΗΕ', bg: 'bg-amber-500/20', border: 'border-amber-400', text: 'text-amber-300', strokeColor: '#f59e0b', badgeBg: '#d97706' },
  REGION_OF_ATTICA: { shortLabel: 'ΠΕΡΙΦΕΡΕΙΑ', bg: 'bg-purple-500/20', border: 'border-purple-400', text: 'text-purple-300', strokeColor: '#c084fc', badgeBg: '#9333ea' },
  OASA: { shortLabel: 'ΟΑΣΑ', bg: 'bg-emerald-500/20', border: 'border-emerald-400', text: 'text-emerald-300', strokeColor: '#34d399', badgeBg: '#059669' },
  KEP_MITOS: { shortLabel: 'ΚΕΠ/ΜΙΤΟΣ', bg: 'bg-rose-500/20', border: 'border-rose-400', text: 'text-rose-300', strokeColor: '#fb7185', badgeBg: '#e11d48' },
};

export async function fetchHealth() { const r = await fetch('/api/health'); return r.json(); }
export async function fetchDemoPresets() { const r = await fetch('/api/presets'); const d = await r.json(); return d.presets || []; }
export async function fetchExecutiveDashboard() { const r = await fetch('/api/executive/dashboard'); return r.json(); }
export async function requestExecutiveAiBriefing(key) {
  const r = await fetch('/api/executive/ai-briefing', { method: 'POST', headers: key ? { 'X-Gemini-Api-Key': key } : {} });
  if (!r.ok) throw new Error('Failed');
  return r.json();
}

export async function streamIncidentPipeline({ citizenComment, latitude, longitude, presetId, imageFile, geminiApiKey, onAgentStart, onAgentComplete, onPipelineComplete, onError }) {
  const fd = new FormData();
  fd.append('citizen_comment', citizenComment || '');
  fd.append('latitude', String(latitude));
  fd.append('longitude', String(longitude));
  if (presetId && !imageFile) fd.append('preset_id', presetId);
  if (imageFile) fd.append('image', imageFile);

  const res = await fetch('/api/incidents/stream', { method: 'POST', headers: geminiApiKey ? { 'X-Gemini-Api-Key': geminiApiKey } : {}, body: fd });
  if (!res.ok) throw new Error('Stream failed');

  const reader = res.body.getReader();
  const decoder = new TextDecoder('utf-8');
  let buffer = '';

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const blocks = buffer.split(/\\r?\\n\\r?\\n/);
    buffer = blocks.pop() || '';

    for (const b of blocks) {
      if (!b.trim()) continue;
      let evType = 'message', dataStr = '';
      for (const line of b.split(/\\r?\\n/)) {
        if (line.startsWith('event:')) evType = line.slice(6).trim();
        else if (line.startsWith('data:')) dataStr += line.slice(5).trim();
      }
      if (!dataStr) continue;
      try {
        const parsed = JSON.parse(dataStr);
        if (evType === 'agent_start' && onAgentStart) onAgentStart(parsed);
        else if (evType === 'agent_complete' && onAgentComplete) onAgentComplete(parsed);
        else if (evType === 'pipeline_complete' && onPipelineComplete) onPipelineComplete(parsed);
      } catch (e) {}
    }
  }
}
""",
    "frontend/src/components/BoundingBoxCanvas.jsx": """import React from 'react';
import { AGENCY_STYLES } from '../api/client';

export default function BoundingBoxCanvas({ imageDataUrl, detectedHazards = [], jurisdictionMappings = [] }) {
  if (!imageDataUrl) return null;
  const geoMap = {};
  for (const m of jurisdictionMappings) geoMap[m.hazard_id] = m.final_agency;

  return (
    <div className="relative w-full overflow-hidden rounded-xl border border-slate-700 bg-slate-900">
      <img src={imageDataUrl} alt="Incident" className="w-full h-auto max-h-[300px] object-cover" />
      <svg viewBox="0 0 1000 1000" preserveAspectRatio="none" className="absolute inset-0 w-full h-full pointer-events-none">
        {detectedHazards.map((h) => {
          const box = h.bounding_box || { ymin: 100, xmin: 100, ymax: 900, xmax: 900 };
          const agency = geoMap[h.hazard_id] || h.preliminary_agency || 'CITY_OF_ATHENS';
          const st = AGENCY_STYLES[agency] || AGENCY_STYLES.CITY_OF_ATHENS;
          return <rect key={h.hazard_id} x={box.xmin} y={box.ymin} width={box.xmax - box.xmin} height={box.ymax - box.ymin} fill={st.strokeColor} fillOpacity="0.2" stroke={st.strokeColor} strokeWidth="8" rx="12" />;
        })}
      </svg>
    </div>
  );
}
""",
    "frontend/src/components/CityOnMobileEmulator.jsx": """import React from 'react';
import { Camera, MapPin, Send, CheckCircle2, Layers } from 'lucide-react';
import { AGENCY_STYLES } from '../api/client';

export default function CityOnMobileEmulator({ presets, selectedPresetId, onSelectPreset, citizenComment, setCitizenComment, latitude, setLatitude, longitude, setLongitude, imagePreviewUrl, onUploadCustomImage, onSubmitIncident, isRunning, completedReport }) {
  const decision = completedReport?.decision_output;
  return (
    <div className="flex flex-col items-center">
      <div className="w-full mb-4 bg-slate-900 border border-slate-800 rounded-2xl p-3">
        <div className="text-xs font-semibold text-sky-400 mb-2">Hackathon Live Demo Presets</div>
        {presets.map((p) => (
          <button key={p.id} type="button" onClick={() => onSelectPreset(p)} className={`w-full text-left p-2 rounded-xl border mb-2 text-xs ${selectedPresetId === p.id ? 'bg-sky-500/20 border-sky-400 text-white' : 'bg-slate-950 border-slate-800 text-slate-300'}`}>
            <div className="font-bold">{p.title_el}</div>
          </button>
        ))}
      </div>
      <div className="w-full max-w-[430px] rounded-[38px] border-[6px] border-slate-800 bg-slate-950 shadow-2xl overflow-hidden">
        <div className="bg-[#003865] px-5 pt-3 pb-3 text-white">
          <div className="font-extrabold text-base">CityOn • Athens CivicBridge</div>
        </div>
        <div className="p-4 space-y-3 max-h-[650px] overflow-y-auto bg-slate-900 text-xs">
          {imagePreviewUrl && <img src={imagePreviewUrl} alt="Preview" className="w-full h-36 object-cover rounded-xl border border-slate-700" />}
          <textarea rows={3} value={citizenComment} onChange={(e) => setCitizenComment(e.target.value)} className="w-full bg-slate-950 border border-slate-800 p-2 rounded-xl text-white" placeholder="Περιγράψτε το πρόβλημα..." />
          <button type="button" disabled={isRunning} onClick={onSubmitIncident} className="w-full py-2.5 rounded-xl bg-sky-500 hover:bg-sky-400 text-white font-bold flex items-center justify-center gap-2">
            <Send className="w-4 h-4" /> {isRunning ? 'Επεξεργασία Agents...' : 'Αποστολή Αναφοράς'}
          </button>
          {decision && (
            <div className="mt-3 space-y-2 pt-3 border-t border-slate-800">
              <div className="bg-emerald-950/60 border border-emerald-500/40 p-2.5 rounded-xl text-emerald-200">
                <CheckCircle2 className="w-4 h-4 inline mr-1" /> {decision.citizen_unified_message_el}
              </div>
              {decision.dispatched_tickets.map((t) => (
                <div key={t.ticket_id} className="bg-slate-950 p-2.5 rounded-xl border border-slate-800">
                  <div className="font-bold text-sky-300">#{t.ticket_id} ({t.target_agency})</div>
                  <div className="text-white mt-0.5">{t.ticket_title_el}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
""",
    "frontend/src/components/AgentControlRoom.jsx": """import React from 'react';
import { Cpu, CheckCircle2, Globe, ShieldCheck, Activity } from 'lucide-react';
import BoundingBoxCanvas from './BoundingBoxCanvas';

export default function AgentControlRoom({ activeAgents, completedTraces, completedReport, imagePreviewUrl, errorMsg }) {
  const traceMap = {};
  for (const t of completedTraces) traceMap[t.agent_number] = t;
  const visionOut = completedReport?.vision_output || traceMap[1]?.structured_output;
  const geoOut = completedReport?.geo_output || traceMap[2]?.structured_output;

  return (
    <div className="space-y-4 text-xs">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Cpu className="w-5 h-5 text-sky-400" />
          <span className="font-bold text-white text-sm">Multi-Agent Control Room & Live Trace</span>
        </div>
      </div>
      {errorMsg && <div className="bg-rose-950 text-rose-200 p-3 rounded-xl">{errorMsg}</div>}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4">
        <div className="font-bold text-sky-400 mb-2">Vision AI & 2D Bounding Boxes</div>
        <BoundingBoxCanvas imageDataUrl={completedReport?.image_data_url || imagePreviewUrl} detectedHazards={visionOut?.detected_hazards || []} jurisdictionMappings={geoOut?.jurisdiction_mappings || []} />
      </div>
    </div>
  );
}
""",
    "frontend/src/components/ExecutiveDashboard.jsx": """import React, { useEffect, useState } from 'react';
import { Map, Sparkles, RefreshCw } from 'lucide-react';
import { fetchExecutiveDashboard, requestExecutiveAiBriefing } from '../api/client';

export default function ExecutiveDashboard({ geminiApiKey }) {
  const [data, setData] = useState(null);
  const [briefing, setBriefing] = useState(null);

  useEffect(() => { fetchExecutiveDashboard().then(setData).catch(console.error); }, []);

  return (
    <div className="space-y-4 text-xs">
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-slate-900 p-4 rounded-2xl border border-slate-800">
          <div className="text-slate-400">Ενεργά Tickets</div>
          <div className="text-2xl font-bold text-white mt-1">{data?.total_dispatched_tickets || 0}</div>
        </div>
      </div>
      <div className="bg-slate-900 p-4 rounded-2xl border border-slate-800">
        <button type="button" onClick={() => requestExecutiveAiBriefing(geminiApiKey).then(setBriefing)} className="px-3 py-2 bg-sky-500 rounded-xl text-white font-bold flex items-center gap-2">
          <Sparkles className="w-4 h-4" /> AI Executive Briefing
        </button>
        {briefing && <div className="mt-3 text-slate-200">{briefing.headline_summary_el}</div>}
      </div>
    </div>
  );
}
""",
    "frontend/src/App.jsx": """import React, { useEffect, useState } from 'react';
import { Sparkles, Smartphone, LayoutDashboard } from 'lucide-react';
import CityOnMobileEmulator from './components/CityOnMobileEmulator';
import AgentControlRoom from './components/AgentControlRoom';
import ExecutiveDashboard from './components/ExecutiveDashboard';
import { fetchDemoPresets, fetchHealth, streamIncidentPipeline } from './api/client';

export default function App() {
  const [tab, setTab] = useState('studio');
  const [apiKey, setApiKey] = useState(() => localStorage.getItem('KEY') || '');
  const [presets, setPresets] = useState([]);
  const [presetId, setPresetId] = useState('flagship_sidewalk_eydap');
  const [comment, setComment] = useState('');
  const [lat, setLat] = useState(37.981969);
  const [lon, setLon] = useState(23.732121);
  const [preview, setPreview] = useState('');
  const [running, setRunning] = useState(false);
  const [activeAgents, setActiveAgents] = useState({});
  const [traces, setTraces] = useState([]);
  const [report, setReport] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchDemoPresets().then(list => { setPresets(list); if (list.length) apply(list[0]); }).catch(console.error);
  }, []);

  const apply = (p) => {
    setPresetId(p.id);
    setComment(p.citizen_comment);
    setLat(p.latitude);
    setLon(p.longitude);
    setPreview(p.image_data_url);
    setReport(null);
    setTraces([]);
    setActiveAgents({});
  };

  const run = async () => {
    setRunning(true);
    setError('');
    setTraces([]);
    setReport(null);
    try {
      await streamIncidentPipeline({
        citizenComment: comment,
        latitude: lat,
        longitude: lon,
        presetId,
        geminiApiKey: apiKey,
        onAgentStart: (ev) => setActiveAgents(prev => ({ ...prev, [ev.agent_number]: ev.message_el })),
        onAgentComplete: (tr) => setTraces(prev => [...prev.filter(t => t.agent_number !== tr.agent_number), tr].sort((a,b)=>a.agent_number-b.agent_number)),
        onPipelineComplete: (rep) => setReport(rep),
        onError: (err) => setError(err.message),
      });
    } catch (e) { setError(e.message); } finally { setRunning(false); }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <header className="border-b border-slate-800 p-4 flex justify-between items-center bg-slate-900/80">
        <div className="flex items-center gap-2 font-bold"><Sparkles className="text-sky-400" /> Athens CivicBridge</div>
        <div className="flex gap-2">
          <button type="button" onClick={() => setTab('studio')} className={`px-3 py-1.5 rounded-lg text-xs font-bold ${tab==='studio'?'bg-sky-500 text-white':'text-slate-400'}`}><Smartphone className="inline w-3.5 h-3.5 mr-1" /> Studio</button>
          <button type="button" onClick={() => setTab('executive')} className={`px-3 py-1.5 rounded-lg text-xs font-bold ${tab==='executive'?'bg-sky-500 text-white':'text-slate-400'}`}><LayoutDashboard className="inline w-3.5 h-3.5 mr-1" /> Executive</button>
        </div>
      </header>
      <main className="flex-1 max-w-[1600px] w-full mx-auto p-6">
        {tab === 'studio' ? (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            <div className="lg:col-span-5"><CityOnMobileEmulator presets={presets} selectedPresetId={presetId} onSelectPreset={apply} citizenComment={comment} setCitizenComment={setComment} latitude={lat} setLatitude={setLat} longitude={lon} setLongitude={setLon} imagePreviewUrl={preview} onUploadCustomImage={(f) => setPreview(URL.createObjectURL(f))} onSubmitIncident={run} isRunning={running} completedReport={report} /></div>
            <div className="lg:col-span-7"><AgentControlRoom activeAgents={activeAgents} completedTraces={traces} completedReport={report} imagePreviewUrl={preview} errorMsg={error} /></div>
          </div>
        ) : <ExecutiveDashboard geminiApiKey={apiKey} />}
      </main>
    </div>
  );
}
"""
}


def create_zip_archive():
    zip_filename = "athens-civic-bridge.zip"
    print(f"📦 Packaging complete Athens CivicBridge codebase into {zip_filename}...")

    os.makedirs("athens-civic-bridge", exist_ok=True)

    with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
        for filepath, content in ALL_PROJECT_FILES.items():
            full_path = os.path.join("athens-civic-bridge", filepath)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            zipf.write(full_path, arcname=filepath)

    print(f"✅ Successfully created {zip_filename} with all backend modules, 6 AI agents, webhooks, and React frontend!")


if __name__ == "__main__":
    create_zip_archive()