import logging
from time import perf_counter

from app.core.config import get_defaults_from_config
from app.db.qdrant import search_docs
from app.llm.generation import LLMGeneration, prompt_generation

logger = logging.getLogger(__name__)


class Lodestone:
    def __init__(
        self,
        request_id: str,
        query: str,
        limit: int,
        k: int,
        mode: str = "retrieval",
        provider: str | None = None,
        rewrite_query: bool = False,
    ):
        self.request_id = request_id
        self.user_query = query
        self.mode = mode
        self.limit = limit
        self.k = k
        self.provider = provider
        self.rewrite_query = rewrite_query
        self.searched_docs = None
        self.ai_mode = LLMGeneration()
        self.new_query = query

        logger.info(
            "lodestone initialised",
            extra={
                "request_id": self.request_id,
                "query": query,
                "limit": limit,
                "k": k,
                "mode": mode,
                "provider": provider,
                "rewrite_query": rewrite_query,
                "rewritten_query": self.new_query,
            },
        )

        self.RESULT = {
            "retrieval": {
                "query": self.user_query,
                "rewritten_query": self.new_query,
                "mode": self.mode,
                "results": [],
                "retrieval_latency_ms": 0.0,
            },
            "ai_response": {
                "ai_answer": None,
                "provider": None,
                "response_latency_ms": 0.0,
            },
            "meta": {
                "request_id": self.request_id,
                "total_latency_ms": None,
            },
        }

    @classmethod
    async def create(cls, request_id, query, limit, k, mode, provider, rewrite_query):
        """Async factory — use instead of __init__ for heavy work."""
        if provider and hasattr(provider, "value"):
            provider = provider.value

        if provider is None:
            defaults = get_defaults_from_config()
            provider = defaults.get("active", {}).get("provider") or None

        instance = cls(request_id, query, limit, k, mode, provider, rewrite_query)

        if rewrite_query and provider is not None:
            instance.new_query = await instance.ai_mode.rewrite_query(query, provider)
            instance.RESULT["retrieval"]["rewritten_query"] = instance.new_query

        _query = instance.new_query if rewrite_query else query

        start = perf_counter()
        instance.searched_docs = await search_docs(
            query=_query,
            limit=instance.limit,
            k=instance.k,
        )
        total = (perf_counter() - start) * 1000
        instance.RESULT["retrieval"]["retrieval_latency_ms"] = round(total, 2)

        logger.info(
            "search completed",
            extra={
                "request_id": instance.request_id,
                "query": _query,
                "doc_count": len(instance.searched_docs),
                "retrieval_latency_ms": total,
            },
        )

        for docs in instance.searched_docs:
            doc_id = docs.get("doc_id", None)
            title = docs.get("title", "")
            source = docs.get("source", "")
            score = docs.get("score", None)
            raw_ce = docs.get("cross_encoder_score", None)
            cross_encoder_score = raw_ce.item() if raw_ce is not None else None
            cross_norm = docs.get("cross_norm", None)
            normalized_score = docs.get("normalized_score", None)
            snippets = docs.get("all_chunks", [])

            res = {
                "doc_id": doc_id,
                "title": title,
                "source": source,
                "normalized_score": normalized_score,
                "score": score,
                "cross_encoder_score": cross_encoder_score,
                "cross_norm": cross_norm,
                "snippets": snippets,
            }
            instance.RESULT["retrieval"]["results"].append(res)

        return instance

    def retrieval_result(self):
        logger.info(
            "retrieval mode returning results",
            extra={
                "request_id": self.request_id,
                "query": self.user_query,
                "rewritten_query": self.new_query,
                "result_count": len(self.RESULT["retrieval"]["results"]),
            },
        )

    async def ai_result(self):
        if self.provider is None:
            logger.warning("LLM provider not given, returning without AI answer")
            return

        logger.info(
            "generating LLM response",
            extra={
                "request_id": self.request_id,
                "provider": self.provider,
                "query": self.new_query,
            },
        )
        prompt = prompt_generation(self.new_query, self.searched_docs)
        llm_response = await self.ai_mode.generate(
            provider=self.provider, prompt=prompt
        )

        self.RESULT["ai_response"]["ai_answer"] = llm_response.text
        self.RESULT["ai_response"]["provider"] = llm_response.provider
        self.RESULT["ai_response"]["response_latency_ms"] = (
            llm_response.response_latency_ms
        )
        if llm_response.status == "success":
            self.RESULT["ai_response"]["llm"] = {
                "prompt_tokens": llm_response.prompt_tokens,
                "completion_tokens": llm_response.completion_tokens,
                "finish_reason": llm_response.finish_reason,
            }
            logger.info(
                "LLM response received",
                extra={
                    "request_id": self.request_id,
                    "provider": llm_response.provider,
                    "response_latency_ms": llm_response.response_latency_ms,
                    "prompt_tokens": llm_response.prompt_tokens,
                    "completion_tokens": llm_response.completion_tokens,
                    "finish_reason": llm_response.finish_reason,
                },
            )
        else:
            self.RESULT["ai_response"]["error"] = {
                "error_code": llm_response.error_code,
                "error": llm_response.error,
                "status": llm_response.status,
            }
            logger.error(
                "error generating llm response",
                extra={
                    "request_id": self.request_id,
                    "provider": llm_response.provider,
                    "error_code": llm_response.error_code,
                    "error": llm_response.error,
                    "status": llm_response.status,
                },
            )

    async def get_results(self):
        self.retrieval_result()
        if self.mode == "ai":
            await self.ai_result()

        self.RESULT["meta"]["total_latency_ms"] = (
            self.RESULT["retrieval"]["retrieval_latency_ms"]
            + self.RESULT["ai_response"]["response_latency_ms"]
        )

        return self.RESULT
