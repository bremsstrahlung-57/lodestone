import asyncio
import logging

from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)
_model: SentenceTransformer | None = None
EMBEDDING_MODEL = "all-MiniLM-L6-v2"


def get_model() -> SentenceTransformer:
    """Creates instance for embedding model"""
    global _model
    if _model is None:
        logger.info("loading embedding model", extra={"model": EMBEDDING_MODEL})
        _model = SentenceTransformer(EMBEDDING_MODEL)
        logger.info("embedding model loaded", extra={"model": EMBEDDING_MODEL})

    return _model


def _embed_sync(text: str) -> list[float]:
    model = get_model()
    embedding = model.encode(text, normalize_embeddings=True, show_progress_bar=False)
    vector = embedding.tolist()
    logger.debug(
        "text embedded", extra={"text_len": len(text), "vector_dim": len(vector)}
    )
    return vector


async def embed(text: str) -> list[float]:
    """Embed given str input"""
    return await asyncio.to_thread(_embed_sync, text)
