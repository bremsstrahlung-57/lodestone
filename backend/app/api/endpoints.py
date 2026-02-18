import logging
from importlib.metadata import version
from typing import Literal, Optional

from fastapi import APIRouter, Query

from app.llm.client import LLMProvider
from app.retrieval.docs_recall import Recall

logger = logging.getLogger(__name__)

router = APIRouter()
APP_VERSION = version("recall")


@router.get("/health")
def health_check():
    logger.debug("health check requested")
    return {
        "status": "ok",
        "version": APP_VERSION,
    }


@router.get("/search")
def search_api(
    query: str = Query(..., min_length=3),
    k: int = Query(3, ge=1),
    limit: int = Query(5, ge=1),
    mode: Literal["retrieval", "ai"] = Query("retrieval"),
    provider: Optional[LLMProvider] = Query(None),
    rewrite_query: bool = Query(False),
):
    logger.info(
        "search request received",
        extra={
            "query": query,
            "mode": mode,
            "limit": limit,
            "k": k,
            "provider": provider,
            "rewrite_query": rewrite_query,
        },
    )

    try:
        recall_init = Recall(
            query=query,
            limit=limit,
            k=k,
            mode=mode,
            provider=provider,
            rewrite_query=rewrite_query,
        )
        result = recall_init.get_results()
        result_count = len(result.get("results", []))
        logger.info(
            "search request completed",
            extra={
                "query": query,
                "mode": mode,
                "result_count": result_count,
                "has_ai_answer": result.get("ai_answer") is not None,
            },
        )
        return result
    except Exception:
        logger.exception(
            "search request failed",
            extra={"query": query, "mode": mode, "provider": provider},
        )
        raise
