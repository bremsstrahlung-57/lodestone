import logging

from app.core.settings import Settings
from app.llm.client import (
    AnthropicLLM,
    BaseLLM,
    GeminiLLM,
    GroqLLM,
    OpenAILLM,
)

settings = Settings()
DEFAULT_OPENAI_API_KEY = settings.openai_api_key
DEFAULT_ANTHROPIC_API_KEY = settings.anthropic_api_key
DEFAULT_GEMINI_API_KEY = settings.gemini_api_key
DEFAULT_GROQ_API_KEY = settings.groq_api_key

DEFAULT_OPENAI_MODEL = settings.openai_model
DEFAULT_ANTHROPIC_MODEL = settings.anthropic_model
DEFAULT_GEMINI_MODEL = settings.gemini_model
DEFAULT_GROQ_MODEL = settings.groq_model

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

        if provider == "openai":
            resolved_model = model or DEFAULT_OPENAI_MODEL
            logger.info("creating Groq LLM client", extra={"model": resolved_model})
            return OpenAILLM(api_key or DEFAULT_OPENAI_API_KEY, resolved_model)

        if provider == "anthropic":
            resolved_model = model or DEFAULT_ANTHROPIC_MODEL
            logger.info("creating Groq LLM client", extra={"model": resolved_model})
            return AnthropicLLM(api_key or DEFAULT_ANTHROPIC_API_KEY, resolved_model)

        logger.error("unsupported LLM provider requested", extra={"provider": provider})
        raise ValueError("Unsupported provider")
