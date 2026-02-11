import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

from google import genai
from google.genai import types
from groq import Groq

from app.core.settings import Settings

logger = logging.getLogger(__name__)

settings = Settings()
DEFAULT_GEMINI_API_KEY = settings.gemini_api_key
DEFAULT_GEMINI_MODEL = settings.gemini_model
DEFAULT_GROQ_API_KEY = settings.groq_api_key
DEFAULT_GROQ_MODEL = settings.groq_model
SYSTEM_PROMPT = """You are a retrieval grounded assistant.
You must answer only using the provided context.
The context comes from user owned documents retrieved via semantic search.
Rules:
Do not use outside knowledge.
Do not guess or fill gaps.
If the context is insufficient, say so explicitly.
Prefer factual, grounded answers.
If multiple documents disagree, mention the disagreement.
Cite evidence implicitly by phrasing, not by adding references.
Do not mention embeddings, vector databases, or chunking.
Your goal is to produce a clear, concise, and accurate answer grounded strictly in the context."""


class LLMProvider(str, Enum):
    gemini = "gemini"
    groq = "groq"


def create_gemini_client(api_key: str):
    return genai.Client(api_key=api_key)


def create_groq_client(api_key: str):
    return Groq(api_key=api_key)


def query_rewriting_prompt(query: str):
    prompt = f"""You are a query rewriter for a semantic search system.
Given a user query, rewrite it to improve retrieval from a vector database while strictly preserving the original meaning and intent.
Guidelines:
- Expand abbreviations and fix spelling errors
- Preserve the original question type and intent exactly
- Do not add information the user did not mention
- Do not convert questions into descriptions or labels
- Do not remove key constraints like "which", "how many", "when", etc.
- If the query is already clear, return it with minimal changes
- Return only the rewritten query, nothing else
User Query:
{query}
"""
    return prompt


@dataclass
class LLMResponse:
    text: str | None
    provider: str
    model: str
    latency_ms: float
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    finish_reason: str | None = None


class BaseLLM(ABC):
    @abstractmethod
    def generate(self, prompt: str):
        pass

    @abstractmethod
    def parse_response(self, raw, latency_ms: float) -> LLMResponse:
        pass

    @abstractmethod
    def query_rewrite(self, query: str) -> str:
        pass


class GeminiLLM(BaseLLM):
    def __init__(self, api_key: str, model: str):
        self.client = create_gemini_client(api_key)
        self.model = model
        logger.info("gemini client initialized", extra={"model": model})

    def generate(self, prompt: str):
        logger.debug(
            "gemini generate called",
            extra={"model": self.model, "prompt_len": len(prompt)},
        )
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
            ),
        )
        logger.debug("gemini generate succeeded")
        return response

    def parse_response(self, raw, latency_ms: float) -> LLMResponse:
        usage = getattr(raw, "usage_metadata", None)
        prompt_tokens = getattr(usage, "prompt_token_count", None)
        completion_tokens = getattr(usage, "candidates_token_count", None)
        finish_reason = raw.candidates[0].finish_reason if raw.candidates else None

        logger.info(
            "gemini response parsed",
            extra={
                "model": self.model,
                "latency_ms": round(latency_ms, 2),
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "finish_reason": finish_reason,
            },
        )

        return LLMResponse(
            text=raw.text,
            provider="gemini",
            model=self.model,
            latency_ms=latency_ms,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            finish_reason=finish_reason,
        )

    def query_rewrite(self, query: str):
        prompt = query_rewriting_prompt(query)

        logger.debug(
            "gemini query rewriting called",
            extra={"user_query": query, "model": self.model, "prompt_len": len(prompt)},
        )
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
        )
        logger.debug(
            "gemini query rewriting succeeded",
            extra={"rewritten_query": response.text},
        )
        return response.text


class GroqLLM(BaseLLM):
    def __init__(self, api_key: str, model: str):
        self.client = create_groq_client(api_key)
        self.model = model
        logger.info("groq client initialized", extra={"model": model})

    def generate(self, prompt: str):
        logger.debug(
            "groq generate called",
            extra={"model": self.model, "prompt_len": len(prompt)},
        )
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )
        logger.debug("groq generate succeeded")
        return response

    def parse_response(self, raw, latency_ms: float) -> LLMResponse:
        usage = raw.usage
        prompt_tokens = usage.prompt_tokens
        completion_tokens = usage.completion_tokens
        finish_reason = raw.choices[0].finish_reason

        logger.info(
            "groq response parsed",
            extra={
                "model": self.model,
                "latency_ms": round(latency_ms, 2),
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "finish_reason": finish_reason,
            },
        )

        return LLMResponse(
            text=raw.choices[0].message.content,
            provider="groq",
            model=self.model,
            latency_ms=latency_ms,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            finish_reason=finish_reason,
        )

    def query_rewrite(self, query: str):
        prompt = query_rewriting_prompt(query)

        logger.debug(
            "groq query rewriting called",
            extra={"model": self.model, "prompt_len": len(prompt)},
        )
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "user", "content": prompt},
            ],
        )
        logger.debug(
            "groq query rewriting succeeded",
            extra={"rewritten_query": response.choices[0].message.content},
        )
        return response.choices[0].message.content
