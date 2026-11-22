import math
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
        overpass_query = f"""
        [out:json][timeout:10];
        (
          way(around:35,{lat},{lon})["highway"];
          node(around:120,{lat},{lon})["amenity"~"school|hospital|kindergarten|clinic|doctors|social_facility"];
          way(around:120,{lat},{lon})["amenity"~"school|hospital|kindergarten|clinic"];
          node(around:60,{lat},{lon})["railway"~"station|subway_entrance|tram_stop"];
        );
        out body;
        """.strip()

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
