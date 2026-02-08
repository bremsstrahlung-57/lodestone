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
    limit: int = Query(5, ge=1, le=50),
    k: int = Query(3, ge=1, le=5),
    mode: Literal["retrieval", "ai"] = Query("retrieval"),
    provider: Optional[LLMProvider] = Query(None),
):
    logger.info(
        "search request received",
        extra={
            "query": query,
            "mode": mode,
            "limit": limit,
            "k": k,
            "provider": provider,
        },
    )

    try:
        result = Recall(
            query=query,
            mode=mode,
            limit=limit,
            k=k,
            provider=provider,
        )
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
