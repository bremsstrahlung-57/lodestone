import logging

from app.core.logging import setup_logging

setup_logging()

logger = logging.getLogger(__name__)

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.endpoints import router
from app.db.qdrant import _assert_embedding_dim, _doc_database, ping_qdrant


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("application startup begun")
    try:
        await _doc_database.connect()
        logger.info("sqlite connection verified")
    except Exception:
        logger.exception("failed to connect to sqlite during startup")
        raise
    try:
        await ping_qdrant()
        logger.info("qdrant connection verified")
    except Exception:
        logger.exception("failed to connect to qdrant during startup")
        raise
    try:
        await _assert_embedding_dim()
        logger.info("embedding dimension check passed")
    except Exception:
        logger.exception("embedding dimension assertion failed during startup")
        raise
    logger.info("application startup complete")
    yield
    await _doc_database.close()
    logger.info("application shutdown")


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")
