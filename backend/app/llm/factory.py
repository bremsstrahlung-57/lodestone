import logging

from app.core.settings import get_settings
from app.llm.client import (
    AnthropicLLM,
    BaseLLM,
    GeminiLLM,
    GroqLLM,
    OpenAILLM,
)

settings = get_settings()
DEFAULT_OPENAI_API_KEY = settings.openai_api_key.get_secret_value() if settings.openai_api_key is not None
DEFAULT_ANTHROPIC_API_KEY = settings.anthropic_api_key.get_secret_value() if settings.anthropic_api_key is not None
DEFAULT_GEMINI_API_KEY = settings.gemini_api_key.get_secret_value() if settings.gemini_api_key is not None
DEFAULT_GROQ_API_KEY = settings.groq_api_key.get_secret_value() if settings.groq_api_key is not None

DEFAULT_OPENAI_MODEL = settings.openai_model
DEFAULT_ANTHROPIC_MODEL = settings.anthropic_model
DEFAULT_GEMINI_MODEL = settings.gemini_model
DEFAULT_GROQ_MODEL = settings.groq_model

logger = logging.getLogger(__name__)


class LLMFactory:
    @staticmethod
    def create(
        provider: str,
    ) -> BaseLLM:
        if provider == "gemini":
            logger.info(
                "creating Gemini LLM client",
                extra={"model": DEFAULT_GEMINI_MODEL},
            )
            return GeminiLLM(DEFAULT_GEMINI_API_KEY, DEFAULT_GEMINI_MODEL)

        if provider == "groq":
            logger.info(
                "creating Groq LLM client",
                extra={"model": DEFAULT_GROQ_MODEL},
            )
            return GroqLLM(DEFAULT_GROQ_API_KEY, DEFAULT_GROQ_MODEL)

        if provider == "openai":
            logger.info(
                "creating OpenAi LLM client",
                extra={"model": DEFAULT_OPENAI_MODEL},
            )
            return OpenAILLM(DEFAULT_OPENAI_API_KEY, DEFAULT_OPENAI_MODEL)

        if provider == "anthropic":
            logger.info(
                "creating Anthropic LLM client",
                extra={"model": DEFAULT_ANTHROPIC_MODEL},
            )
            return AnthropicLLM(DEFAULT_ANTHROPIC_API_KEY, DEFAULT_ANTHROPIC_MODEL)

        logger.error("unsupported LLM provider requested", extra={"provider": provider})
        raise ValueError("Unsupported provider")
