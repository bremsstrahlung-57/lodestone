import logging

from app.llm.client import (
    DEFAULT_GEMINI_API_KEY,
    DEFAULT_GEMINI_MODEL,
    DEFAULT_GROQ_API_KEY,
    DEFAULT_GROQ_MODEL,
    BaseLLM,
    GeminiLLM,
    GroqLLM,
)

logger = logging.getLogger(__name__)


class LLMFactory:
    @staticmethod
    def create(
        provider: str,
        api_key: str | None,
        model: str | None,
    ) -> BaseLLM:
        if provider == "gemini":
            resolved_model = model or DEFAULT_GEMINI_MODEL
            logger.info("creating Gemini LLM client", extra={"model": resolved_model})
            return GeminiLLM(api_key or DEFAULT_GEMINI_API_KEY, resolved_model)

        if provider == "groq":
            resolved_model = model or DEFAULT_GROQ_MODEL
            logger.info("creating Groq LLM client", extra={"model": resolved_model})
            return GroqLLM(api_key or DEFAULT_GROQ_API_KEY, resolved_model)

        logger.error("unsupported LLM provider requested", extra={"provider": provider})
        raise ValueError("Unsupported provider")
