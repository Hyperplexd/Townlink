import httpx
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
