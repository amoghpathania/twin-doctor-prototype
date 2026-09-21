"""LLM client interface. Swappable provider; app uses Gemini, tests use a fake implementation."""

from typing import Protocol

from app.config import get_settings

# OpenAPI-subset schema mirroring app.models.schemas.ClinicalAssessment, enforced by Gemini
# itself (not just requested via prose) so structurally invalid output can't come back.
CLINICAL_ASSESSMENT_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "symptoms": {"type": "ARRAY", "items": {"type": "STRING"}},
        # NOTE: "maxItems" is not a recognized field in this SDK version's Schema conversion and
        # raises at request time if added here - the "at most one" rule is enforced via prose only.
        "missing_information": {"type": "ARRAY", "items": {"type": "STRING"}},
        "risk_level": {"type": "STRING", "enum": ["GREEN", "AMBER", "RED"]},
        "escalation_required": {"type": "BOOLEAN"},
        "escalation_reason": {"type": "STRING", "nullable": True},
        "summary": {"type": "STRING"},
        "recommended_action": {"type": "STRING"},
        "confidence": {"type": "NUMBER"},
    },
    "required": [
        "symptoms",
        "missing_information",
        "risk_level",
        "escalation_required",
        "summary",
        "recommended_action",
        "confidence",
    ],
}

MEMORY_EXTRACTION_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "candidates": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "memory_type": {
                        "type": "STRING",
                        "enum": [
                            "preference",
                            "escalation_rule",
                            "communication_style",
                            "clinical_pattern",
                            "workflow_preference",
                        ],
                    },
                    "content": {"type": "STRING"},
                    "confidence": {"type": "NUMBER"},
                },
                "required": ["memory_type", "content", "confidence"],
            },
        }
    },
    "required": ["candidates"],
}

TEST_RECOMMENDATION_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "recommendations": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "catalog_code": {"type": "STRING"},
                    "clinical_indication": {"type": "STRING"},
                    "confidence": {"type": "NUMBER"},
                    "evidence_summary": {"type": "STRING", "nullable": True},
                },
                "required": ["catalog_code", "clinical_indication", "confidence"],
            },
        }
    },
    "required": ["recommendations"],
}


class LLMClient(Protocol):
    def generate_assessment(self, system_instruction: str, prompt: str) -> str:
        """Return raw JSON text matching the ClinicalAssessment schema."""
        ...

    def generate_memories(self, system_instruction: str, prompt: str) -> str:
        """Return raw JSON text matching the memory extraction schema."""
        ...

    def generate_test_recommendations(self, system_instruction: str, prompt: str) -> str:
        """Return raw JSON text matching the diagnostic test recommendation schema."""
        ...


class LLMConfigurationError(RuntimeError):
    """Raised when the configured LLM provider cannot be initialized."""


class GeminiLLMClient:
    """Calls Gemini in JSON mode. Requires GEMINI_API_KEY to be configured."""

    def __init__(self) -> None:
        settings = get_settings()
        if not settings.gemini_api_key:
            raise LLMConfigurationError("GEMINI_API_KEY is not configured")

        import google.generativeai as genai

        genai.configure(api_key=settings.gemini_api_key)
        self._genai = genai
        self._model_name = settings.gemini_model

    def generate_assessment(self, system_instruction: str, prompt: str) -> str:
        # New model per call so system_instruction (persona) is scoped to this doctor/request only.
        model = self._genai.GenerativeModel(self._model_name, system_instruction=system_instruction)
        response = model.generate_content(
            prompt,
            generation_config={
                "response_mime_type": "application/json",
                "response_schema": CLINICAL_ASSESSMENT_SCHEMA,
            },
        )
        return response.text

    def generate_memories(self, system_instruction: str, prompt: str) -> str:
        model = self._genai.GenerativeModel(self._model_name, system_instruction=system_instruction)
        response = model.generate_content(
            prompt,
            generation_config={
                "response_mime_type": "application/json",
                "response_schema": MEMORY_EXTRACTION_SCHEMA,
            },
        )
        return response.text

    def generate_test_recommendations(self, system_instruction: str, prompt: str) -> str:
        model = self._genai.GenerativeModel(self._model_name, system_instruction=system_instruction)
        response = model.generate_content(
            prompt,
            generation_config={
                "response_mime_type": "application/json",
                "response_schema": TEST_RECOMMENDATION_SCHEMA,
            },
        )
        return response.text
