from datetime import datetime
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
