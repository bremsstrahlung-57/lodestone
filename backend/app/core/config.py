from pathlib import Path

import toml
from pydantic import BaseModel

from app.llm.client import LLMProvider

content = """
[groq]
default = "llama-3.3-70b-versatile"
models = [
  "llama-3.3-70b-versatile",
  "llama-3.1-8b-instant",
  "mixtral-8x7b-32768",
  "gemma-7b-it"
]

[openai]
default = "gpt-4.1"
models = [
  "gpt-5.4",
  "gpt-5.4-thinking",
  "gpt-4.1",
  "gpt-4.1-nano",
]

[anthropic]
default = "claude-haiku-4.5"
models = [
  "claude-opus-4.6",
  "claude-sonnet-4.6",
  "claude-haiku-4.5"
]

[google]
default = "gemini-2.5-flash-lite"
models = [
  "gemini-3.1-pro",
  "gemini-2.5-pro",
  "gemini-2.5-flash-lite"
]
""".strip()

config = """
[database]
url="http://localhost:8092"

[active]
provider = ""
model = ""

[providers.openai]
key = "openai"

[providers.groq]
key = "groq"

[providers.anthropic]
key = "anthropic"

[providers.google]
key = "google"
"""

keys = """
[api_keys]
# openai = "YOUR-KEY"
"""

BASE_DIR = Path(__file__).resolve().parent.parent
REGISTRY_PATH = BASE_DIR / "registry" / "models.toml"
registry_path = Path(REGISTRY_PATH)
registry_path.parent.mkdir(parents=True, exist_ok=True)
CONFIG_DIR = Path.home() / ".config" / "lodestone"
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
config_path = CONFIG_DIR / "config.toml"
api_keys_path = CONFIG_DIR / "keys.toml"

if not registry_path.exists():
    registry_path.write_text(content)
if not config_path.exists():
    config_path.write_text(config)
if not api_keys_path.exists():
    api_keys_path.write_text(keys)


def create_registry_file():
    BASE_DIR = Path(__file__).resolve().parent.parent
    REGISTRY_PATH = BASE_DIR / "registry" / "models.toml"
    registry_path = Path(REGISTRY_PATH)
    registry_path.parent.mkdir(parents=True, exist_ok=True)

    if not registry_path.exists():
        registry_path.write_text(content)


def create_config_keys_file():
    CONFIG_DIR = Path.home() / ".config" / "lodestone"
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    config_path = CONFIG_DIR / "config.toml"
    api_keys_path = CONFIG_DIR / "keys.toml"

    if not config_path.exists():
        config_path.write_text(config)
    if not api_keys_path.exists():
        api_keys_path.write_text(keys)


def validate_config_files():
    create_registry_file()
    create_config_keys_file()


def get_all_providers():
    try:
        with open(registry_path, "r") as f:
            registry = toml.load(f)
            providers = []
            for i in registry:
                providers.append(i)
            return providers
    except FileNotFoundError:
        create_registry_file()
        return get_all_providers()


def get_default_model_from_reg(provider: str):
    try:
        with open(registry_path, "r") as f:
            reg = toml.load(f)
            return reg.get(provider, {}).get("default")
    except FileNotFoundError:
        create_registry_file()
        return get_default_model_from_reg(provider)


def get_all_models(provider: str):
    try:
        with open(registry_path, "r") as f:
            reg = toml.load(f)
            return reg.get(provider, {}).get("models")
    except FileNotFoundError:
        create_registry_file()
        return get_all_models(provider)


def get_all_info_for_ai_api():
    try:
        with open(registry_path, "r") as f:
            return toml.load(f)
    except FileNotFoundError:
        create_registry_file()
        return get_all_info_for_ai_api()


def get_defaults_from_config():
    try:
        with open(config_path, "r") as f:
            data = toml.load(f)
            return data
    except FileNotFoundError:
        create_config_keys_file()
        return get_defaults_from_config()


def get_provider_api_key_from_keys(provider):
    if provider is None:
        return None

    try:
        with open(api_keys_path, "r") as f:
            data = toml.load(f)
            keys = data.get("api_keys", {}).get(provider)
            return keys
    except FileNotFoundError:
        create_config_keys_file()
        return get_provider_api_key_from_keys(provider)


# Post req
class APIKeyRequest(BaseModel):
    provider: LLMProvider
    key: str


class APIDefaultAIRequest(BaseModel):
    provider: LLMProvider
    model: str


def save_default_model(provider, model):
    with open(config_path) as f:
        config = toml.load(f)

    config["active"]["provider"] = provider.value

    with open(registry_path, "r") as f:
        check_model = toml.load(f)

    if model in check_model[provider.value]["models"]:
        config["active"]["model"] = model
    else:
        config["active"]["model"] = check_model[provider.value]["default"]

    with open(config_path, "w") as f:
        toml.dump(config, f)


def add_api_key(provider, key):
    with open(api_keys_path, "r") as f:
        config = toml.load(f)

    if "api_keys" not in config:
        config["api_keys"] = {}

    config["api_keys"][provider.value] = key

    with open(api_keys_path, "w") as f:
        toml.dump(config, f)
