from importlib.metadata import version
from typing import Literal, Optional

from fastapi import APIRouter, Query

from app.llm.client import LLMProvider
from app.retrieval.docs_recall import Recall

router = APIRouter()
APP_VERSION = version("recall")


@router.get("/health")
def health_check():
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
    return Recall(
        query=query,
        mode=mode,
        limit=limit,
        k=k,
        provider=provider,
    )
