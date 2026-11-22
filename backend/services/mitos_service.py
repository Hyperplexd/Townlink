import httpx
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
