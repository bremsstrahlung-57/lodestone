import logging
from pathlib import Path

from app.core.logging import setup_logging
from app.db.qdrant import ingest_data
from app.db.sqlitedb import SQLiteDB
from app.ingest.chunking import chunk_text
from app.ingest.doc_id import make_doc_id

setup_logging()


logger = logging.getLogger(__name__)

db_action = SQLiteDB()


def extract_pdf(path: str):
    from pypdf import PdfReader

    reader = PdfReader(path)
    text = "\n".join(page.extract_text() or "" for page in reader.pages)

    return text, {"title": Path(path).stem, "source_type": "pdf", "path": path}


def extract_docx(path: str) -> str:
    from docx import Document

    doc = Document(path)
    text =  "\n".join(p.text for p in doc.paragraphs)

    return text, {"title": Path(path).stem, "source_type": "pdf", "path": path}

def extract_txt(path: str):
    text = Path(path).read_text(encoding="utf-8")

    return text, {
        "title": Path(path).stem,
        "source_type": "txt",
        "path": path
    }



async def ingest_text_core(text: str, source="user", title=None, metadata=None):
    await db_action.connect()

    doc_id = make_doc_id(text)
    chunks = chunk_text(text)
    total_chunks = len(chunks)
    if title is None:
        title = text[:10]
    title = title.strip()

    logger.info(
        "ingesting",
        extra={
            "doc_id": doc_id,
            "source": source,
            "total_chunks": total_chunks,
        },
    )

    await db_action.insert_doc_ib_db(
        doc_id=doc_id,
        title=title,
        content=text,
        source=source,
        total_chunks=total_chunks,
    )

    docs = [
        {
            "doc_id": doc_id,
            "text": c["text"],
            "chunk_id": c["chunk_id"],
        }
        for c in chunks
    ]

    await ingest_data(docs)

    logger.info(
        "ingestion complete", extra={"doc_id": doc_id, "total_chunks": total_chunks}
    )

    await db_action.close()


def extract_text(path: str):
    ext = Path(path).suffix.lower()

    if ext == ".pdf":
        return extract_pdf(path)
    elif ext == ".docx":
        return extract_docx(path)
    elif ext == ".txt":
        return extract_txt(path)
    else:
        raise ValueError("unsupported file")


async def ingest_file(path: str, source="user"):
    text, metadata = extract_text(path)

    await ingest_text_core(
        text=text,
        source=source,
        title=metadata["title"],
        metadata=metadata
    )


async def ingest_text(text: str, source="user"):
    await ingest_text_core(text=text, source=source)
