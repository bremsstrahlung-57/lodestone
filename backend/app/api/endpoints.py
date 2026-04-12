import logging
import os
import shutil
import tempfile
import time
from importlib.metadata import version
from typing import Literal, Optional

from fastapi import APIRouter, File, HTTPException, Query, UploadFile, status
from fastapi.responses import JSONResponse

from app.core.config import (
    APIDefaultAIRequest,
    APIKeyRequest,
    add_api_key,
    get_all_models,
    get_all_providers,
    get_defaults_from_config,
    save_default_model,
)
from app.db.sqlitedb import SQLiteDB
from app.ingest.doc_id import generate_request_id
from app.ingest.ingestion import ingest_file, ingest_text
from app.llm.client import LLMProvider
from app.retrieval.docs_lodestone import Lodestone

logger = logging.getLogger(__name__)

router = APIRouter()
APP_VERSION = version("lodestone")


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

        lodestone_init = await Lodestone.create(
            request_id=request_id,
            query=query,
            limit=limit,
            k=k,
            mode=mode,
            provider=provider,
            rewrite_query=rewrite_query,
        )

        result = await lodestone_init.get_results()
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
                "error": str(e),
            },
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/service_providers")
async def _get_service_providers():
    try:
        logger.info("service_providers request received")
        return {"status": "success", "providers": get_all_providers()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models")
async def _get_all_models(provider: LLMProvider):
    try:
        models = get_all_models(provider)
        if not models:
            raise HTTPException(status_code=404, detail="No models found for provider")

        return {"status": "success", "provider": provider.value, "models": models}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/defaults_config")
async def get_defaults():
    try:
        return {"status": "success", "data": get_defaults_from_config()}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to load defaults")


@router.post("/add_api", status_code=status.HTTP_201_CREATED)
async def add_modify_api_key(req: APIKeyRequest):
    try:
        add_api_key(req.provider, req.key)
        return {
            "status": "success",
            "message": f"API key stored for {req.provider.value}",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/add_default_model", status_code=status.HTTP_201_CREATED)
async def default_provider_and_model(req: APIDefaultAIRequest):
    try:
        save_default_model(req.provider, req.model)
        return {
            "status": "success",
            "message": f"Default model saved {req.provider.value}: {req.model}",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest", status_code=status.HTTP_201_CREATED)
async def upload_and_ingest(file: UploadFile = File(...)):
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = os.path.join(temp_dir, file.filename)
            with open(temp_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            await ingest_file(path=temp_path, source="user")

        return {"status": "success", "message": f"Ingested {file.filename}"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/document/{doc_id}")
async def get_document_content(doc_id: str):
    try:
        db = SQLiteDB()
        content = await db.get_whole_file_data(doc_id)
        await db.close()

        if content is None:
            raise HTTPException(status_code=404, detail="Document not found")

        return {"status": "success", "content": content}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
