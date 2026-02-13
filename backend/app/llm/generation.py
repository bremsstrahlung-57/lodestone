import logging
import time

from app.llm.client import LLMResponse
from app.llm.factory import LLMFactory
from app.retrieval.retrieve import llm_context_builder

logger = logging.getLogger(__name__)


class LLMGeneration:
    def generate(
        self,
        provider: str,
        prompt: str,
        api_key: str | None = None,
        model: str | None = None,
    ) -> LLMResponse:
        logger.info(
            "starting LLM generation",
            extra={"provider": provider, "model": model, "prompt_length": len(prompt)},
        )

        llm = LLMFactory.create(
            provider=provider,
            api_key=api_key,
            model=model,
        )

        start = time.perf_counter()
        try:
            raw = llm.generate(prompt)
        except Exception:
            latency_ms = (time.perf_counter() - start) * 1000
            logger.exception(
                "LLM generation failed",
                extra={"provider": provider, "model": model, "latency_ms": latency_ms},
            )
            raise
        latency_ms = (time.perf_counter() - start) * 1000

        response = llm.parse_response(raw, latency_ms)

        logger.info(
            "LLM generation complete",
            extra={
                "provider": response.provider,
                "model": response.model,
                "latency_ms": response.latency_ms,
                "prompt_tokens": response.prompt_tokens,
                "completion_tokens": response.completion_tokens,
                "finish_reason": response.finish_reason,
            },
        )

        return response

    def rewrite_query(
        self,
        query: str,
        provider: str,
        api_key: str | None = None,
        model: str | None = None,
    ) -> str:
        logger.info(
            "starting query rewriting",
            extra={"user_query": query, "provider": provider, "model": model},
        )

        llm = LLMFactory.create(
            provider=provider,
            api_key=api_key,
            model=model,
        )
        rewritten_query = llm.query_rewrite(query)
        return rewritten_query if rewritten_query is not None else query


def prompt_generation(query, result):
    context = llm_context_builder(query, result)
    prompt = [
        "Query:",
        query,
        "Context:",
        "The following is a list of text chunks retrieved from documents.",
        "Each chunk is independent and may overlap.",
    ]
    for res in context["context"]:
        title = res["title"]
        score = res["score"]
        source = res["source"]
        chunks = res["chunks"]
        chunk = f"Title: {title} | Score: {score} | Source: {source}\nText/Docs/Chunks: {chunks}\n"
        prompt.append(chunk)

    prompt.append("""Task:
Using only the information in the context above, answer the query.
Do not add information that is not present.
Do not explain why an answer is correct. Only state the answer itself.""")

    built = "\n".join(prompt)
    logger.debug(
        "prompt generated",
        extra={
            "query": query,
            "context_docs": len(context["context"]),
            "prompt_length": len(built),
        },
    )
    return built


def llm_provider(default=None):
    llm_providers = ["gemini", "groq"]

    if default is not None:
        logger.debug("using provided LLM provider", extra={"provider": default})
        return default
    elif default not in llm_providers:
        pass

    logger.warning("no LLM provider specified, falling back to interactive selection")
    print("API Available\n1.Gemini\n2.LLama(Groq)")
    num = int(input("Choose provider: "))
    match num:
        case 1:
            logger.info("user selected gemini provider")
            return "gemini"
        case 2:
            logger.info("user selected groq provider")
            return "groq"
        case _:
            logger.info("invalid selection, defaulting to groq provider")
            return "groq"
