"""Shared FastAPI dependencies for API routers."""

import logging

from app.agents.llm_client import GeminiLLMClient, LLMClient, LLMConfigurationError

logger = logging.getLogger(__name__)


class _UnavailableLLMClient:
    def __init__(self, error: LLMConfigurationError) -> None:
        self.error = error

    def generate_assessment(self, system_instruction: str, prompt: str) -> str:
        raise self.error

    def generate_memories(self, system_instruction: str, prompt: str) -> str:
        raise self.error


def get_llm_client() -> LLMClient:
    """Overridden in tests with a fake client; real app resolves Gemini from settings."""
    try:
        return GeminiLLMClient()
    except LLMConfigurationError as exc:
        logger.error("Gemini client initialization failed: %s", exc)
        return _UnavailableLLMClient(exc)
