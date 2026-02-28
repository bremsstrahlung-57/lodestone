import logging
from pathlib import Path

from app.core.logging import setup_logging

setup_logging()

from app.db.qdrant import ingest_data
from app.db.sqlitedb import SQLiteDB
from app.ingest.chunking import chunk_text
from app.ingest.doc_id import make_doc_id

logger = logging.getLogger(__name__)

db_action = SQLiteDB()


async def ingest_file(path: str, source="user"):
    """File ingestion for Vector DB"""
    await db_action.connect()
    logger.info("ingesting file", extra={"path": path, "source": source})

    try:
        text = Path(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        logger.exception("file not found", extra={"path": path})
        raise
    except OSError:
        logger.exception("failed to read file", extra={"path": path})
        raise

    title = Path(path).stem
    doc_id = make_doc_id(text)
    chunks = chunk_text(text)
    total_chunks = chunks[-1].get("chunk_id", 0) + 1

    logger.info(
        "file chunked",
        extra={
            "path": path,
            "title": title,
            "doc_id": doc_id,
            "total_chunks": total_chunks,
        },
    )

    await db_action.insert_doc_ib_db(
        doc_id=doc_id,
        title=title.strip(),
        content=text,
        source=source,
        total_chunks=total_chunks,
    )

    docs = []
    for c in chunks:
        docs.append(
            {
                "doc_id": doc_id,
                "text": c["text"],
                "chunk_id": c["chunk_id"],
            }
        )

    await ingest_data(docs)
    logger.info(
        "file ingestion complete",
        extra={"doc_id": doc_id, "total_chunks": total_chunks},
    )
    await db_action.close()


async def ingest_text(text: str):
    """Text ingestiong for Vector DB"""
    await db_action.connect()
    doc_id = make_doc_id(text)
    chunks = chunk_text(text)
    total_chunks = len(chunks)

    logger.info(
        "ingesting text",
        extra={
            "doc_id": doc_id,
            "text_length": len(text),
            "total_chunks": total_chunks,
        },
    )

    docs = []
    for c in chunks:
        docs.append(
            {
                "doc_id": doc_id,
                "text": c["text"],
                "chunk_id": c["chunk_id"],
            }
        )

    await ingest_data(docs)
    logger.info(
        "text ingestion complete",
        extra={"doc_id": doc_id, "total_chunks": total_chunks},
    )
    await db_action.close()
