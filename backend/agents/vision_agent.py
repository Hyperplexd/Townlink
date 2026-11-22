from typing import Optional
from agents.base import BaseCivicAgent
from models.schemas import VisionTriageOutput

VISION_SYSTEM_INSTRUCTION = """
Είσαι ο Agent 1 (VisionTriageAgent) του συστήματος TownLink.
Εντόπισε όλα τα διακριτά προβλήματα υποδομής, υπολόγισε 2D bounding boxes (0-1000) και υποστήριξε multi-agency splitting.
""".strip()


class VisionTriageAgent(BaseCivicAgent):
    def __init__(self) -> None:
        super().__init__(1, "vision_triage_agent", "Agent 1: Πολυτροπικός Vision AI Agent")

    async def analyze(self, citizen_comment: str, image_bytes: Optional[bytes] = None, image_mime_type: str = "image/jpeg") -> VisionTriageOutput:
        prompt = f"""Ανάλυσε την αναφορά πολίτη: '{citizen_comment}'"""
        return await self.generate_structured(prompt, VisionTriageOutput, VISION_SYSTEM_INSTRUCTION, image_bytes, image_mime_type, temperature=0.1)
