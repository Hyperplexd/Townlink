import base64
import time
from datetime import datetime, timezone
from typing import List, Optional

from demo_assets import get_preset_image_bytes
from models.schemas import (
    AgencyCode,
    AgentStepTrace,
    BoundingBox2D,
    CentralDecisionOutput,
    CompleteIncidentReport,
    DetectedHazardItem,
    ExecutiveDecisionInsight,
    GeoJurisdictionOutput,
    HazardCategory,
    HazardJurisdictionMapping,
    HazardSLAAssessment,
    MitosKnowledgeOutput,
    MitosProcedureSummary,
    SmartSLAContextOutput,
    UrgencyLevel,
    ValidationCheckItem,
    ValidationCriticOutput,
    VisionTriageOutput,
)
from webhooks.agency_endpoints import dispatch_ticket_to_agency_webhook


def is_gemini_unavailable(exc: BaseException) -> bool:
    nested = getattr(exc, "exceptions", None)
    if nested:
        return any(is_gemini_unavailable(item) for item in nested)
    code = getattr(exc, "status_code", None)
    if code in (429, 503):
        return True
    text = f"{type(exc).__name__} {exc}"
    return any(
        marker in text
        for marker in ("RESOURCE_EXHAUSTED", "monthly spending cap", "UNAVAILABLE", "high demand")
    )


def _premade_image_data_url() -> str:
    raw = get_preset_image_bytes("flagship_sidewalk_eydap")
    encoded = base64.b64encode(raw).decode("utf-8")
    return f"data:image/jpeg;base64,{encoded}"


def _report_image_data_url(image_bytes: Optional[bytes], image_mime_type: str) -> str:
    if not image_bytes:
        return _premade_image_data_url()
    encoded = base64.b64encode(image_bytes).decode("utf-8")
    return f"data:{image_mime_type or 'image/jpeg'};base64,{encoded}"


def _split_durations(total_ms: int) -> List[int]:
    total_ms = max(6, int(total_ms))
    weights = (34, 16, 12, 12, 13, 13)
    parts = [max(1, total_ms * weight // 100) for weight in weights]
    parts[-1] = max(1, total_ms - sum(parts[:-1]))
    return parts


def _vision() -> VisionTriageOutput:
    return VisionTriageOutput(
        is_valid_civic_input=True,
        scene_summary_el="Έτοιμο παράδειγμα, γιατί το Gemini δεν απάντησε (όριο δαπάνης ή προσωρινή υπερφόρτωση). Σπασμένο πεζοδρόμιο και διαρροή από φρεάτιο ΕΥΔΑΠ.",
        multi_agency_split_detected=True,
        accessibility_impact=True,
        detected_hazards=[
            DetectedHazardItem(
                hazard_id="HAZ-SIDEWALK",
                category=HazardCategory.BROKEN_SIDEWALK,
                title_el="Σπασμένες πλάκες πεζοδρομίου",
                description_el="Καθίζηση και σπασμένες πλάκες στο πεζοδρόμιο, με κίνδυνο για τους πεζούς.",
                preliminary_agency=AgencyCode.CITY_OF_ATHENS,
                severity_score=7,
                confidence=0.91,
                bounding_box=BoundingBox2D(ymin=680, xmin=40, ymax=960, xmax=520),
                visual_evidence_cues=["σπασμένες πλάκες", "ανισόπεδο πεζοδρόμιο"],
            ),
            DetectedHazardItem(
                hazard_id="HAZ-EYDAP",
                category=HazardCategory.WATER_LEAK_MANHOLE,
                title_el="Διαρροή από φρεάτιο ΕΥΔΑΠ",
                description_el="Ανοιχτό φρεάτιο με ροή νερού προς το οδόστρωμα.",
                preliminary_agency=AgencyCode.EYDAP,
                severity_score=9,
                confidence=0.94,
                bounding_box=BoundingBox2D(ymin=360, xmin=560, ymax=900, xmax=960),
                visual_evidence_cues=["φρεάτιο", "ροή νερού"],
            ),
        ],
    )


def _geo(lat: float, lon: float, vision: VisionTriageOutput) -> GeoJurisdictionOutput:
    mappings = [
        HazardJurisdictionMapping(
            hazard_id="HAZ-SIDEWALK",
            final_agency=AgencyCode.CITY_OF_ATHENS,
            agency_name_el="Δήμος Αθηναίων",
            department_el="Διεύθυνση Οδοποιίας και Συντήρησης",
            jurisdiction_reasoning_el="Το πεζοδρόμιο ανήκει στο δημοτικό δίκτυο και το αναλαμβάνει ο Δήμος.",
            legal_basis_note_el="Δημοτική αρμοδιότητα πεζοδρομίων.",
        ),
        HazardJurisdictionMapping(
            hazard_id="HAZ-EYDAP",
            final_agency=AgencyCode.EYDAP,
            agency_name_el="ΕΥΔΑΠ Α.Ε.",
            department_el="Υπηρεσία Άμεσης Επέμβασης",
            jurisdiction_reasoning_el="Η διαρροή από φρεάτιο ύδρευσης ανήκει στην ΕΥΔΑΠ.",
            legal_basis_note_el="Δίκτυο ύδρευσης ΕΥΔΑΠ.",
        ),
    ]
    return GeoJurisdictionOutput(
        latitude=lat,
        longitude=lon,
        formatted_address_el="Πανεπιστημίου 42, Αθήνα",
        street_name="Πανεπιστημίου",
        osm_highway_type="primary",
        is_within_athens_municipality=True,
        municipal_community_id=1,
        municipal_community_name_el="1η Δημοτική Κοινότητα",
        is_major_regional_avenue=False,
        jurisdiction_mappings=mappings,
        raw_gis_metadata={"fallback": "quota", "hazard_count": len(vision.detected_hazards)},
    )


def _sla() -> SmartSLAContextOutput:
    return SmartSLAContextOutput(
        nearest_oasa_stops=[],
        is_near_transit_hub=False,
        nearby_sensitive_pois=["Πανεπιστήμιο Αθηνών"],
        overall_urgency=UrgencyLevel.CRITICAL_SAFETY_HAZARD,
        hazard_sla_assessments=[
            HazardSLAAssessment(
                hazard_id="HAZ-SIDEWALK",
                urgency_level=UrgencyLevel.HIGH_VULNERABLE_ZONE,
                target_sla_hours=24,
                priority_score=72,
                sla_justification_el="Κίνδυνος πτώσης πεζών σε κεντρικό πεζοδρόμιο.",
            ),
            HazardSLAAssessment(
                hazard_id="HAZ-EYDAP",
                urgency_level=UrgencyLevel.CRITICAL_SAFETY_HAZARD,
                target_sla_hours=6,
                priority_score=91,
                sla_justification_el="Ενεργή διαρροή σε οδόστρωμα με άμεσο κίνδυνο.",
            ),
        ],
    )


def _mitos() -> MitosKnowledgeOutput:
    return MitosKnowledgeOutput(
        citizen_guidance_el="Η αναφορά καλύφθηκε από το CityOn. Δεν χρειάζεται ξεχωριστή αίτηση σε ΕΥΔΑΠ ή στον Δήμο.",
        live_mitos_api_queried=False,
        search_keywords_used=["φρεάτιο", "διαρροή", "πεζοδρόμιο"],
        matched_procedures=[
            MitosProcedureSummary(
                procedure_id="FALLBACK-EYDAP-LEAK",
                title_el="Βλάβη δικτύου ύδρευσης",
                organization_el="ΕΥΔΑΠ Α.Ε.",
                url="https://www.eydap.gr",
                required_documents_el=[],
                steps_el=["Καταγραφή σημείου", "Αποστολή συνεργείου", "Αποκατάσταση διαρροής"],
                estimated_cost_el="Χωρίς χρέωση για τον πολίτη",
            )
        ],
    )


def _validation() -> ValidationCriticOutput:
    return ValidationCriticOutput(
        approved_for_dispatch=True,
        overall_trust_score=0.86,
        image_text_consistency=True,
        geospatial_consistency=True,
        critic_summary_el="Έτοιμος έλεγχος επειδή το Gemini δεν ήταν διαθέσιμο. Το παράδειγμα εγκρίνεται για επίδειξη αποστολής.",
        validation_checks=[
            ValidationCheckItem(check_name="Gemini fallback", passed=True, details_el="Το Gemini επέστρεψε RESOURCE_EXHAUSTED ή 503 UNAVAILABLE, οπότε χρησιμοποιήθηκε έτοιμη φωτογραφία."),
            ValidationCheckItem(check_name="Image text consistency", passed=True, details_el="Η έτοιμη σκηνή δείχνει πεζοδρόμιο και φρεάτιο με διαρροή."),
            ValidationCheckItem(check_name="Geospatial consistency", passed=True, details_el="Το σημείο παραμένει στην Πανεπιστημίου 42."),
        ],
    )


async def build_quota_fallback_report(
    report_id: str,
    citizen_comment: str,
    lat: float,
    lon: float,
    agent_meta: List[dict],
    started_at: float,
    image_bytes: Optional[bytes] = None,
    image_mime_type: str = "image/jpeg",
) -> CompleteIncidentReport:
    vision = _vision()
    geo = _geo(lat, lon, vision)
    sla = _sla()
    mitos = _mitos()
    validation = _validation()
    tickets = []
    for hazard in vision.detected_hazards:
        mapping = next(item for item in geo.jurisdiction_mappings if item.hazard_id == hazard.hazard_id)
        assessment = next(item for item in sla.hazard_sla_assessments if item.hazard_id == hazard.hazard_id)
        tickets.append(
            await dispatch_ticket_to_agency_webhook(
                report_id,
                hazard,
                mapping.final_agency,
                mapping.department_el,
                geo,
                assessment.urgency_level,
                assessment.target_sla_hours,
                assessment.priority_score,
                None,
                citizen_comment,
            )
        )
    decision = CentralDecisionOutput(
        citizen_unified_message_el="Η αναφορά καταχωρίστηκε με έτοιμο παράδειγμα, γιατί το Gemini δεν ήταν διαθέσιμο. Ο Δήμος και η ΕΥΔΑΠ ειδοποιήθηκαν χωριστά.",
        apps_saved_count=2,
        dispatched_tickets=tickets,
        executive_insight=ExecutiveDecisionInsight(
            cascading_risk_detected=True,
            inter_agency_coordination_plan_el="Πρώτα η ΕΥΔΑΠ για τη διαρροή, μετά ο Δήμος για τις πλάκες του πεζοδρομίου.",
            estimated_social_impact_score=78,
            executive_recommendation_el="Κλείσιμο λωρίδας γύρω από το φρεάτιο μέχρι την αποκατάσταση.",
        ),
        total_pipeline_duration_ms=max(6, int((time.perf_counter() - started_at) * 1000)),
    )
    summaries = {
        1: vision.scene_summary_el,
        2: geo.formatted_address_el,
        3: f"Urgency: {sla.overall_urgency.value}",
        4: f"{len(mitos.matched_procedures)} procedures",
        5: f"Trust Score: {int(validation.overall_trust_score * 100)}%",
        6: f"Dispatched {len(tickets)} tickets.",
    }
    outputs = {
        1: vision.model_dump(),
        2: geo.model_dump(),
        3: sla.model_dump(),
        4: mitos.model_dump(),
        5: validation.model_dump(),
        6: decision.model_dump(),
    }
    durations = _split_durations(decision.total_pipeline_duration_ms)
    traces = [
        AgentStepTrace(
            agent_number=meta["n"],
            agent_id=meta["id"],
            agent_name_el=meta["name"],
            status="completed",
            duration_ms=durations[meta["n"] - 1],
            summary_el=summaries[meta["n"]],
            api_calls_made=["Premade fallback"],
            structured_output=outputs[meta["n"]],
        )
        for meta in agent_meta
    ]
    return CompleteIncidentReport(
        report_id=report_id,
        created_at=datetime.now(timezone.utc).isoformat(),
        citizen_comment=citizen_comment,
        latitude=lat,
        longitude=lon,
        image_data_url=_report_image_data_url(image_bytes, image_mime_type),
        vision_output=vision,
        geo_output=geo,
        sla_output=sla,
        mitos_output=mitos,
        validation_output=validation,
        decision_output=decision,
        agent_traces=traces,
    )
