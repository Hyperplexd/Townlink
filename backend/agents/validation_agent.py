from agents.base import BaseCivicAgent
from models.schemas import GeoJurisdictionOutput, MitosKnowledgeOutput, SmartSLAContextOutput, ValidationCriticOutput, VisionTriageOutput

VAL_SYSTEM_INSTRUCTION = """Είσαι ο Agent 5 (ValidationCriticAgent). Έλεγχος εγκυρότητας.""".strip()


class ValidationCriticAgent(BaseCivicAgent):
    def __init__(self) -> None:
        super().__init__(5, "validation_critic_agent", "Agent 5: Guardrail Validator")

    async def validate_pipeline(self, citizen_comment: str, vision_output: VisionTriageOutput, geo_output: GeoJurisdictionOutput, sla_output: SmartSLAContextOutput, mitos_output: MitosKnowledgeOutput) -> ValidationCriticOutput:
        prompt = f"""Validate pipeline for: {citizen_comment}"""
        return await self.generate_structured(prompt, ValidationCriticOutput, VAL_SYSTEM_INSTRUCTION, temperature=0.1)
