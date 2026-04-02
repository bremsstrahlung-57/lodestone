import tomllib
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
REGISTRY_PATH = BASE_DIR / "registry" / "models.toml"

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
  "o3",
  "o3-mini"
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

path = Path(REGISTRY_PATH)
path.parent.mkdir(parents=True, exist_ok=True)
if not path.exists():
    path.write_text(content)


def get_all_providers():
    with open(path, "rb") as f:
        registry = tomllib.load(f)
        providers = []
        for i in registry:
            providers.append(i)
        return providers


def get_default_model(provider: str):
    with open(path, "rb") as f:
        reg = tomllib.load(f)
        return reg.get(provider, {}).get("default")


def get_all_models(provider: str):
    with open(path, "rb") as f:
        reg = tomllib.load(f)
        return reg.get(provider, {}).get("models")


def get_all_info_for_ai_api():
    with open(path, "rb") as f:
        return tomllib.load(f)
