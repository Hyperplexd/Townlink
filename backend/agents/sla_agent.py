from typing import Any, Dict, List
from agents.base import BaseCivicAgent
from models.schemas import GeoJurisdictionOutput, SmartSLAContextOutput, VisionTriageOutput
from services.oasa_service import oasa_service

SLA_SYSTEM_INSTRUCTION = """Είσαι ο Agent 3 (SmartSLAContextAgent). Υπολόγισε Smart SLA και κοντινές στάσεις ΟΑΣΑ.""".strip()


class SmartSLAContextAgent(BaseCivicAgent):
    def __init__(self) -> None:
        super().__init__(3, "smart_sla_context_agent", "Agent 3: Smart SLA & OASA Context Agent")

    async def evaluate_sla(self, lat: float, lon: float, vision_output: VisionTriageOutput, geo_output: GeoJurisdictionOutput, live_geo_context: Dict[str, Any]) -> tuple[SmartSLAContextOutput, List[Dict[str, Any]]]:
        stops = await oasa_service.get_closest_oasa_stops(lat, lon)
        prompt = f"""OASA Stops: {stops}\nVision: {vision_output.model_dump_json()}"""
        res = await self.generate_structured(prompt, SmartSLAContextOutput, SLA_SYSTEM_INSTRUCTION, temperature=0.15)
        return res, stops
