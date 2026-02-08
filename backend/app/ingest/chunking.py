import logging

logger = logging.getLogger(__name__)


def chunk_text(text: str, chunk_size: int = 512, overlap: int = 128):
    """Chunk text"""
    if len(text) <= chunk_size:
        logger.debug("text fits in single chunk, skipping splitting")
        return [text]

    chunks = []
    start = 0
    chunk_id = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]

        chunks.append(
            {
                "chunk_id": chunk_id,
                "text": chunk,
            }
        )

        chunk_id += 1
        start += chunk_size - overlap

    logger.debug(
        "text chunked",
        extra={
            "text_length": len(text),
            "chunk_size": chunk_size,
            "overlap": overlap,
            "total_chunks": len(chunks),
        },
    )
    return chunks
