import logging

from app.db.qdrant import search_docs
from app.llm.generation import LLMGeneration, prompt_generation

logger = logging.getLogger(__name__)


class Recall:
    def __init__(
        self,
        query: str,
        limit: int,
        k: int,
        mode: str = "retrieval",
        provider: str | None = None,
        rewrite_query: bool = False,
    ):
        self.user_query = query
        self.mode = mode
        self.limit = limit
        self.k = k
        self.provider = provider
        self.rewrite_query = rewrite_query
        self.searched_docs = None
        self.ai_mode = LLMGeneration()
        self.new_query = (
            self.ai_mode.rewrite_query(self.user_query, self.provider)
            if rewrite_query and provider is not None
            else self.user_query
        )

        logger.info(
            "recall initialised",
            extra={
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
            "query": self.user_query,
            "rewritten_query": self.new_query,
            "mode": self.mode,
            "results": [],
            "ai_answer": None,
            "provider": None,
            "latency_ms": None,
        }

        _query = self.user_query
        if self.rewrite_query:
            _query = self.new_query

        self.searched_docs = search_docs(query=_query, limit=self.limit, k=self.k)
        logger.info(
            "search completed",
            extra={"query": _query, "doc_count": len(self.searched_docs)},
        )

        for docs in self.searched_docs:
            doc_id = docs.get("doc_id", None)
            title = docs.get("title", "")
            source = docs.get("source", "")
            score = docs.get("score", None)
            snippets = docs.get("all_chunks", [])

            res = {
                "doc_id": doc_id,
                "title": title,
                "source": source,
                "score": score,
                "snippets": snippets,
            }
            self.RESULT["results"].append(res)

    def retrieval_result(self):
        logger.info(
            "retrieval mode returning results",
            extra={
                "query": self.user_query,
                "rewritten_query": self.new_query,
                "result_count": len(self.RESULT["results"]),
            },
        )

    def ai_result(self):
        if self.provider is None:
            logger.warning("LLM provider not given, returning without AI answer")
            return

        logger.info(
            "generating LLM response",
            extra={"provider": self.provider, "query": self.new_query},
        )
        prompt = prompt_generation(self.new_query, self.searched_docs)
        llm_response = self.ai_mode.generate(provider=self.provider, prompt=prompt)

        self.RESULT["ai_answer"] = llm_response.text
        self.RESULT["provider"] = llm_response.provider
        self.RESULT["latency_ms"] = llm_response.latency_ms
        self.RESULT["llm"] = {
            "prompt_tokens": llm_response.prompt_tokens,
            "completion_tokens": llm_response.completion_tokens,
            "finish_reason": llm_response.finish_reason,
        }

        logger.info(
            "LLM response received",
            extra={
                "provider": llm_response.provider,
                "latency_ms": llm_response.latency_ms,
                "prompt_tokens": llm_response.prompt_tokens,
                "completion_tokens": llm_response.completion_tokens,
                "finish_reason": llm_response.finish_reason,
            },
        )

    def get_results(self):
        self.retrieval_result()
        if self.mode == "ai":
            self.ai_result()

        return self.RESULT
