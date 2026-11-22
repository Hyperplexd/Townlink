import json
from typing import Any, Dict
from agents.base import BaseCivicAgent
from models.schemas import GeoJurisdictionOutput, VisionTriageOutput
from services.gis_osm_service import gis_osm_service

GEO_SYSTEM_INSTRUCTION = """Είσαι ο Agent 2 (GeoJurisdictionAgent). Καθορίσε τελική αρμοδιότητα.""".strip()


class GeoJurisdictionAgent(BaseCivicAgent):
    def __init__(self) -> None:
        super().__init__(2, "geo_jurisdiction_agent", "Agent 2: GIS & OSM Jurisdiction Resolver")

    async def resolve_jurisdiction(self, lat: float, lon: float, vision_output: VisionTriageOutput) -> tuple[GeoJurisdictionOutput, Dict[str, Any]]:
        live_geo = await gis_osm_service.inspect_location(lat, lon)
        prompt = f"""GIS Context: {json.dumps(live_geo)} \n Vision: {vision_output.model_dump_json()}"""
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
