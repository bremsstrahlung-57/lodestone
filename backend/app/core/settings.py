import os
from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings

from app.core.config import (
    get_default_model_from_reg,
    get_defaults_from_config,
    get_provider_api_key_from_keys,
)


class Settings(BaseSettings):
    qdrant_url: str = "http://localhost:8092"

    openai_api_key: SecretStr | None = None
    anthropic_api_key: SecretStr | None = None
    google_api_key: SecretStr | None = None
    groq_api_key: SecretStr | None = None

    openai_model: str = "gpt-4.1"
    anthropic_model: str = "claude-haiku-4.5"
    google_model: str = "google-3-flash"
    groq_model: str = "llama-3.3-70b-versatile"


@lru_cache
def get_settings() -> Settings:
    config_data = get_defaults_from_config() or {}

    db_config = config_data.get("database", {})

    kwargs = {}
    qdrant_url = db_config.get("url")
    if qdrant_url and not os.environ.get("QDRANT_URL"):
        kwargs["qdrant_url"] = qdrant_url

    return Settings(
        **kwargs,
        openai_api_key=get_provider_api_key_from_keys("openai") or None,
        anthropic_api_key=get_provider_api_key_from_keys("anthropic") or None,
        google_api_key=get_provider_api_key_from_keys("google") or None,
        groq_api_key=get_provider_api_key_from_keys("groq") or None,
        openai_model=get_default_model_from_reg("openai") or "gpt-4.1",
        anthropic_model=get_default_model_from_reg("anthropic") or "claude-haiku-4.5",
        google_model=get_default_model_from_reg("google") or "google-3-flash",
        groq_model=get_default_model_from_reg("groq") or "llama-3.3-70b-versatile",
    )
