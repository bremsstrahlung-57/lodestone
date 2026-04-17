import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

from anthropic import APIConnectionError as AnthropicConnectionError
from anthropic import APIStatusError as AnthropicStatusError
from anthropic import AsyncAnthropic
from anthropic import RateLimitError as AnthropicRateLimitError
from anthropic.types import TextBlock
from google import genai
from google.genai import types
from google.genai.errors import ClientError as GoogleClientError
from groq import APIConnectionError as GroqConnectionError
from groq import APIError as GroqAPIError
from groq import AsyncGroq
from groq import AuthenticationError as GroqAuthenticationError
from groq import RateLimitError as GroqRateLimitError
from openai import APIConnectionError as OpenAIConnectionError
from openai import APIStatusError as OpenAIStatusError
from openai import AsyncOpenAI
from openai import RateLimitError as OpenAIRateLimitError

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
You are a document-grounded assistant. Your answers come exclusively from the retrieved context — the user's personal documents. You don't use outside knowledge.

Talk like a person, not a manual. When you explain something, explain it the way you'd tell a friend — clear, grounded, no unnecessary formality. If the context doesn't have enough to answer, say so plainly, like "I don't see anything in your documents about that." If documents contradict each other, call it out naturally — "interestingly, one document says X but another says Y." Be direct and concise. Never surface implementation details like embeddings, vectors, scores, or chunk IDs.
"""


class LLMProvider(str, Enum):
    google = "google"
    groq = "groq"
    openai = "openai"
    anthropic = "anthropic"


def query_rewriting_prompt(query):
    return f"""
You are a query rewriting engine. You have one job: take the user's search query and rewrite it so it retrieves better results from a semantic search system.

Expand abbreviations, fix typos, unpack shorthand into plain language — but leave the intent exactly as it was. Don't add context the user didn't imply, don't explain what you changed, don't respond conversationally. Output only the rewritten query.

Examples:
- "mc of gow" → "main character of God of War"
- "RAG in AI" → "Retrieval-Augmented Generation in AI"
- "best wpns in ds3" → "best weapons in Dark Souls 3"
- "how to beat nameless king" → "how to beat Nameless King"

<user_query>
{query}
</user_query>

Rewritten query:"""


@dataclass
class LLMResponse:
    text: str | None
    provider: str
    model: str
    response_latency_ms: float = 0.0
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    finish_reason: str | None = None
    error_code: str | None = None
    error: str | None = None
    status: str = "success"


class BaseLLM(ABC):
    @abstractmethod
    async def generate(self, prompt: str) -> LLMResponse:
        pass

    @abstractmethod
    async def query_rewrite(self, query: str) -> str:
        pass


class GoogleLLM(BaseLLM):
    def __init__(self, api_key: str | None, model: str):
        if api_key:
            self.client = genai.Client(api_key=api_key)
        else:
            self.client = None

        self.apiprovider = "google"
        self.model = model
        logger.info(f"{self.apiprovider} client initialized", extra={"model": model})

    async def generate(self, prompt: str) -> LLMResponse:
        logger.debug(
            f"{self.apiprovider} generate called",
            extra={"model": self.model, "prompt_len": len(prompt)},
        )

        start = time.perf_counter()
        try:
            if self.client is None:
                logger.error(f"{self.apiprovider} api key is none")
                return LLMResponse(
                    text=None,
                    provider=self.apiprovider,
                    model=self.model,
                    error_code=404,
                    error=f"Can't find API Key of {self.apiprovider}.",
                    status="API_KEY_NOT_FOUND_OR_SET",
                )

            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                ),
            )

            usage = getattr(response, "usage_metadata", None)
            prompt_tokens = getattr(usage, "prompt_token_count", None)
            completion_tokens = getattr(usage, "candidates_token_count", None)
            finish_reason = (
                response.candidates[0].finish_reason if response.candidates else None
            )

            latency_ms = (time.perf_counter() - start) * 1000

            logger.debug(
                f"{self.apiprovider} response finished generating",
                extra={
                    "model": self.model,
                    "response_latency_ms": round(latency_ms, 2),
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "finish_reason": finish_reason,
                },
            )

            return LLMResponse(
                text=response.text,
                provider=self.apiprovider,
                model=self.model,
                response_latency_ms=latency_ms,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                finish_reason=finish_reason,
            )
        except GoogleClientError as e:
            error_code = str(getattr(e, "status_code", getattr(e, "code", None)))
            error = str(e)
            status = str(getattr(e, "status", "CLIENT_ERROR"))

            logger.error(
                f"error generating {self.apiprovider} response",
                extra={
                    "model": self.model,
                    "error_code": error_code,
                    "error": error,
                    "status": status,
                },
            )

            return LLMResponse(
                text=None,
                provider=self.apiprovider,
                model=self.model,
                error_code=error_code,
                error=error,
                status=status,
            )

        except Exception as e:
            logger.error(
                f"error generating {self.apiprovider} response",
                extra={
                    "model": self.model,
                    "error_code": None,
                    "error": str(e),
                    "status": "UNKNOWN_ERROR",
                },
            )
            return LLMResponse(
                text=None,
                provider=self.apiprovider,
                model=self.model,
                error_code=None,
                error=str(e),
                status="UNKNOWN_ERROR",
            )

    async def query_rewrite(self, query: str):
        prompt = query_rewriting_prompt(query)

        logger.debug(
            f"{self.apiprovider} query rewriting called",
            extra={"user_query": query, "model": self.model, "prompt_len": len(prompt)},
        )
        try:
            if self.client is None:
                logger.error(f"{self.apiprovider} api key is none")
                return query

            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=prompt,
            )

            logger.debug(
                f"{self.apiprovider} query rewriting succeeded",
                extra={"rewritten_query": response.text},
            )
            return response.text if response.text else query

        except Exception as e:
            logger.error(
                f"{self.apiprovider} query rewriting failed, returning default",
                extra={"error": e},
            )
            return query


class GroqLLM(BaseLLM):
    def __init__(self, api_key: str | None, model: str):
        if api_key:
            self.client = AsyncGroq(api_key=api_key)
        else:
            self.client = None

        self.model = model
        self.apiprovider = "groq"
        logger.info(f"{self.apiprovider} client initialized", extra={"model": model})

    async def generate(self, prompt: str) -> LLMResponse:
        logger.debug(
            f"{self.apiprovider} generate called",
            extra={"model": self.model, "prompt_len": len(prompt)},
        )

        start = time.perf_counter()
        try:
            if self.client is None:
                logger.error(f"{self.apiprovider} api key is none")
                return LLMResponse(
                    text=None,
                    provider=self.apiprovider,
                    model=self.model,
                    error_code=404,
                    error=f"Can't find API Key of {self.apiprovider}.",
                    status="API_KEY_NOT_FOUND_OR_SET",
                )

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
            )

            latency_ms = (time.perf_counter() - start) * 1000
            usage = response.usage
            prompt_tokens = usage.prompt_tokens if usage else None
            completion_tokens = usage.completion_tokens if usage else None
            finish_reason = (
                response.choices[0].finish_reason if response.choices else None
            )

            logger.debug(
                "google response finished generating",
                extra={
                    "model": self.model,
                    "response_latency_ms": round(latency_ms, 2),
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "finish_reason": finish_reason,
                },
            )

            return LLMResponse(
                text=response.choices[0].message.content,
                provider=self.apiprovider,
                model=self.model,
                response_latency_ms=latency_ms,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                finish_reason=finish_reason,
            )
        except GroqRateLimitError as e:
            error_code = str(e.status_code)
            error = str(e.message)
            status = "RATE_LIMIT"

            logger.error(
                f"error generating {self.apiprovider} response",
                extra={
                    "model": self.model,
                    "error_code": error_code,
                    "error": error,
                    "status": status,
                },
            )

            return LLMResponse(
                text=None,
                provider=self.apiprovider,
                model=self.model,
                error_code=error_code,
                error=error,
                status=status,
            )
        except GroqConnectionError as e:
            error_code = None
            error = str(e.message)
            status = "CONNECTION_ERROR"

            logger.error(
                f"error generating {self.apiprovider} response",
                extra={
                    "model": self.model,
                    "error_code": error_code,
                    "error": error,
                    "status": status,
                },
            )

            return LLMResponse(
                text=None,
                provider=self.apiprovider,
                model=self.model,
                error_code=error_code,
                error=error,
                status=status,
            )
        except GroqAuthenticationError as e:
            error_code = str(e.status_code)
            error = str(e.message)
            status = "AUTH_ERROR"

            logger.error(
                f"error generating {self.apiprovider} response",
                extra={
                    "model": self.model,
                    "error_code": error_code,
                    "error": error,
                    "status": status,
                },
            )

            return LLMResponse(
                text=None,
                provider=self.apiprovider,
                model=self.model,
                error_code=error_code,
                error=error,
                status=status,
            )
        except GroqAPIError as e:
            error_code = getattr(e, "status_code", None)
            error = str(e.message)
            status = "API_ERROR"

            logger.error(
                f"error generating {self.apiprovider} response",
                extra={
                    "model": self.model,
                    "error_code": error_code,
                    "error": error,
                    "status": status,
                },
            )

            return LLMResponse(
                text=None,
                provider=self.apiprovider,
                model=self.model,
                error_code=error_code,
                error=error,
                status=status,
            )
        except Exception as e:
            logger.error(
                f"error generating {self.apiprovider} response",
                extra={
                    "model": self.model,
                    "error_code": None,
                    "error": str(e),
                    "status": "UNKNOWN_ERROR",
                },
            )
            return LLMResponse(
                text=None,
                provider=self.apiprovider,
                model=self.model,
                error_code=None,
                error=str(e),
                status="UNKNOWN_ERROR",
            )

    async def query_rewrite(self, query: str):
        prompt = query_rewriting_prompt(query)

        logger.debug(
            "groq query rewriting called",
            extra={"model": self.model, "prompt_len": len(prompt)},
        )
        try:
            if self.client is None:
                logger.error(f"{self.apiprovider} api key is none")
                return query

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt},
                ],
            )
            logger.debug(
                "groq query rewriting succeeded",
                extra={"rewritten_query": response.choices[0].message.content},
            )
            return (
                response.choices[0].message.content
                if response.choices[0].message.content
                else query
            )

        except Exception as e:
            logger.error(
                f"{self.apiprovider} query rewriting failed, returning default",
                extra={"error": e},
            )
            return query


class OpenAILLM(BaseLLM):
    def __init__(self, api_key: str | None, model: str):
        if api_key:
            self.client = AsyncOpenAI(api_key=api_key)
        else:
            self.client = None
        self.apiprovider = "openai"
        self.model = model
        logger.info(
            f"{self.apiprovider} client initialized",
            extra={"model": model},
        )

    async def generate(self, prompt: str) -> LLMResponse:
        logger.debug(
            f"{self.apiprovider} generate called",
            extra={"model": self.model, "prompt_len": len(prompt)},
        )
        start = time.perf_counter()
        try:
            if self.client is None:
                logger.error(f"{self.apiprovider} api key is none")
                return LLMResponse(
                    text=None,
                    provider=self.apiprovider,
                    model=self.model,
                    error_code=404,
                    error=f"Can't find API Key of {self.apiprovider}.",
                    status="API_KEY_NOT_FOUND_OR_SET",
                )

            response = await self.client.responses.create(
                model=self.model,
                input=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
            )

            usage = getattr(response, "usage", None)
            prompt_tokens = getattr(usage, "input_tokens", None)
            completion_tokens = getattr(usage, "output_tokens", None)
            output = getattr(response, "output", None) or []
            output_item = next(
                (item for item in output if hasattr(item, "finish_reason")), None
            )
            finish_reason = getattr(output_item, "finish_reason", None)

            latency_ms = (time.perf_counter() - start) * 1000

            logger.debug(
                f"{self.apiprovider} response finished generating",
                extra={
                    "model": self.model,
                    "response_latency_ms": round(latency_ms, 2),
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "finish_reason": finish_reason,
                },
            )

            return LLMResponse(
                text=response.output_text,
                provider=self.apiprovider,
                model=self.model,
                response_latency_ms=latency_ms,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                finish_reason=finish_reason,
            )

        except OpenAIRateLimitError as e:
            logger.error(
                f"error generating {self.apiprovider} response",
                extra={
                    "model": self.model,
                    "error_code": "429",
                    "error": str(e),
                    "status": "rate_limit",
                },
            )

            return LLMResponse(
                text=None,
                provider=self.apiprovider,
                model=self.model,
                error_code="429",
                error=str(e),
                status="rate_limit",
            )

        except OpenAIStatusError as e:
            error_code = str(e.status_code)
            error = e.message
            status = e.__class__.__name__

            logger.error(
                f"error generating {self.apiprovider} response",
                extra={
                    "model": self.model,
                    "error_code": error_code,
                    "error": error,
                    "status": status,
                },
            )

            return LLMResponse(
                text=None,
                provider=self.apiprovider,
                model=self.model,
                error_code=error_code,
                error=error,
                status="error",
            )

        except OpenAIConnectionError as e:
            logger.error(
                f"error generating {self.apiprovider} response",
                extra={
                    "model": self.model,
                    "error_code": None,
                    "error": str(e),
                    "status": "connection_error",
                },
            )

            return LLMResponse(
                text=None,
                provider=self.apiprovider,
                model=self.model,
                error_code=None,
                error=str(e),
                status="connection_error",
            )

        except Exception as e:
            logger.error(
                f"error generating {self.apiprovider} response",
                extra={
                    "model": self.model,
                    "error_code": None,
                    "error": str(e),
                    "status": "UNKNOWN_ERROR",
                },
            )
            return LLMResponse(
                text=None,
                provider=self.apiprovider,
                model=self.model,
                error_code=None,
                error=str(e),
                status="UNKNOWN_ERROR",
            )

    async def query_rewrite(self, query: str):
        prompt = query_rewriting_prompt(query)

        logger.debug(
            f"{self.apiprovider} query rewriting called",
            extra={"user_query": query, "model": self.model, "prompt_len": len(prompt)},
        )
        try:
            if self.client is None:
                logger.error(f"{self.apiprovider} api key is none")
                return query

            response = await self.client.responses.create(
                model=self.model,
                input=prompt,
            )

            logger.debug(
                f"{self.apiprovider} query rewriting succeeded",
                extra={"rewritten_query": response.text},
            )
            return response.output_text if response.output_text else query

        except Exception as e:
            logger.error(
                f"{self.apiprovider} query rewriting failed, returning default",
                extra={"error": e},
            )
            return query


class AnthropicLLM(BaseLLM):
    def __init__(self, api_key: str | None, model: str):
        if api_key:
            self.client = AsyncAnthropic(api_key=api_key)
        else:
            self.client = None

        self.apiprovider = "anthropic"
        self.model = model
        logger.info(f"{self.apiprovider} client initialized", extra={"model": model})

    async def generate(self, prompt: str) -> LLMResponse:
        logger.debug(
            f"{self.apiprovider} generate called",
            extra={"model": self.model, "prompt_len": len(prompt)},
        )

        start = time.perf_counter()
        try:
            if self.client is None:
                logger.error(f"{self.apiprovider} api key is none")
                return LLMResponse(
                    text=None,
                    provider=self.apiprovider,
                    model=self.model,
                    error_code=404,
                    error=f"Can't find API Key of {self.apiprovider}.",
                    status="API_KEY_NOT_FOUND_OR_SET",
                )

            response = await self.client.messages.create(
                model=self.model,
                max_tokens=256,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )

            usage = response.usage
            prompt_tokens = getattr(usage, "input_tokens", None)
            completion_tokens = getattr(usage, "output_tokens", None)
            finish_reason = response.stop_reason

            latency_ms = (time.perf_counter() - start) * 1000

            logger.debug(
                f"{self.apiprovider} response finished generating",
                extra={
                    "model": self.model,
                    "response_latency_ms": round(latency_ms, 2),
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "finish_reason": finish_reason,
                },
            )

            text = next(
                (
                    block.text
                    for block in response.content
                    if isinstance(block, TextBlock)
                ),
                None,
            )

            return LLMResponse(
                text=text,
                provider=self.apiprovider,
                model=self.model,
                response_latency_ms=latency_ms,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                finish_reason=finish_reason,
            )
        except AnthropicRateLimitError as e:
            logger.error(
                f"error generating {self.apiprovider} response",
                extra={
                    "model": self.model,
                    "error_code": "429",
                    "error": str(e),
                    "status": "RATE_LIMIT_ERROR",
                },
            )
            return LLMResponse(
                text=None,
                provider=self.apiprovider,
                model=self.model,
                error_code="429",
                error=str(e),
                status="RATE_LIMIT_ERROR",
            )

        except AnthropicStatusError as e:
            logger.error(
                f"error generating {self.apiprovider} response",
                extra={
                    "model": self.model,
                    "error_code": str(e.status_code),
                    "error": str(e),
                    "status": "API_STATUS_ERROR",
                },
            )
            return LLMResponse(
                text=None,
                provider=self.apiprovider,
                model=self.model,
                error_code=str(e.status_code),
                error=str(e),
                status="API_STATUS_ERROR",
            )

        except AnthropicConnectionError as e:
            logger.error(
                f"error generating {self.apiprovider} response",
                extra={
                    "model": self.model,
                    "error_code": None,
                    "error": str(e),
                    "status": "CONNECTION_ERROR",
                },
            )
            return LLMResponse(
                text=None,
                provider=self.apiprovider,
                model=self.model,
                error_code=None,
                error=str(e),
                status="CONNECTION_ERROR",
            )

        except Exception as e:
            logger.error(
                f"error generating {self.apiprovider} response",
                extra={
                    "model": self.model,
                    "error_code": None,
                    "error": str(e),
                    "status": "UNKNOWN_ERROR",
                },
            )
            return LLMResponse(
                text=None,
                provider=self.apiprovider,
                model=self.model,
                error_code=None,
                error=str(e),
                status="UNKNOWN_ERROR",
            )

    async def query_rewrite(self, query: str):
        prompt = query_rewriting_prompt(query)

        logger.debug(
            f"{self.apiprovider} query rewriting called",
            extra={"user_query": query, "model": self.model, "prompt_len": len(prompt)},
        )
        try:
            if self.client is None:
                logger.error(f"{self.apiprovider} api key is none")
                return query

            response = await self.client.messages.create(
                model=self.model,
                max_tokens=256,
                messages=[{"role": "user", "content": prompt}],
            )

            rewritten = next(
                (
                    block.text
                    for block in response.content
                    if isinstance(block, TextBlock)
                ),
                None,
            )

            logger.debug(
                f"{self.apiprovider} query rewriting succeeded",
                extra={"rewritten_query": rewritten},
            )
            return rewritten if rewritten else query

        except Exception as e:
            logger.error(
                f"{self.apiprovider} query rewriting failed, returning default",
                extra={"error": e},
            )
            return query
