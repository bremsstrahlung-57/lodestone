import logging
import time
from importlib.metadata import version
from typing import Literal, Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from app.ingest.doc_id import generate_request_id
from app.llm.client import LLMProvider
from app.retrieval.docs_recall import Recall

logger = logging.getLogger(__name__)

router = APIRouter()
APP_VERSION = version("recall")


@router.get("/health")
async def health_check():
    logger.debug("health check requested")
    return {
        "status": "ok",
        "version": APP_VERSION,
    }


@router.get("/search")
async def search_api(
    query: str = Query(..., min_length=3),
    k: int = Query(5, ge=1),
    limit: int = Query(50, ge=5),
    mode: Literal["retrieval", "ai"] = Query("retrieval"),
    provider: Optional[LLMProvider] = Query(None),
    rewrite_query: bool = Query(False),
):
    start_time = time.perf_counter()

    try:
        request_id = generate_request_id()
        logger.info(
            "search request received",
            extra={
                "request_id": request_id,
                "query": query,
                "mode": mode,
                "limit": limit,
                "k": k,
                "provider": provider,
                "rewrite_query": rewrite_query,
            },
        )

        recall_init = await Recall.create(
            request_id=request_id,
            query=query,
            limit=limit,
            k=k,
            mode=mode,
            provider=provider,
            rewrite_query=rewrite_query,
        )

        result = await recall_init.get_results()
        total_latency = (time.perf_counter() - start_time) * 1000

        headers = {
            "X-Request-ID": request_id,
            "X-Response-Time": f"{round(total_latency, 2)}ms",
        }

        logger.info(
            "search request completed",
            extra={
                "request_id": request_id,
                "query": query,
                "mode": mode,
                "result_count": len(result.get("retrieval", {}).get("results", [])),
                "has_ai_answer": result.get("ai_response", {}).get("ai_answer")
                is not None,
            },
        )

        return JSONResponse(content=result, headers=headers)

    except Exception as e:
        logger.exception(
            "search request failed",
            extra={
                "request_id": request_id,
                "query": query,
                "error": e,
            },
        )
        raise HTTPException(status_code=500, detail="Internal Server Error")
