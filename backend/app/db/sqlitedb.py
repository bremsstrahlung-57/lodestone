import logging
import os
from datetime import datetime

import aiosqlite

DATA_PATH = "data/"
DATA_FILE_PATH = "data/data.db"


logger = logging.getLogger(__name__)


def make_cache_folder():
    try:
        os.mkdir(DATA_PATH)
        logger.info("cache directory created", extra={"path": DATA_PATH})
    except FileExistsError:
        logger.debug("cache directory already exists", extra={"path": DATA_PATH})
    except FileNotFoundError:
        logger.error(
            "parent directory does not exist",
            extra={"path": DATA_PATH},
            exc_info=True,
        )
        raise


class SQLiteDB:
    def __init__(self) -> None:
        logger.info("initializing SQLite database")
        self._db: aiosqlite.Connection | None = None

    async def _ensure_connected(self) -> None:
        """Lazily initialize the database connection if not already connected."""
        if self._db is None:
            await self.connect()

    async def connect(self) -> None:
        make_cache_folder()
        self._db = await aiosqlite.connect(DATA_FILE_PATH)
        await self._db.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                doc_id TEXT PRIMARY KEY,
                title TEXT,
                content TEXT NOT NULL,
                source TEXT,
                total_chunks INTEGER,
                created_at TEXT
            );
        """)
        await self._db.commit()

    async def close(self) -> None:
        if self._db:
            await self._db.close()
            self._db = None

    async def insert_doc_ib_db(
        self, doc_id: str, title: str, content: str, source: str, total_chunks: int
    ):
        await self._ensure_connected()
        iso_format = iso_format = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            await self._db.execute(
                "INSERT OR REPLACE INTO documents VALUES(?, ?, ?, ?, ?, ?)",
                (doc_id, title, content, source, total_chunks, iso_format),
            )
            await self._db.commit()

            logger.info(
                "document saved",
                extra={
                    "doc_id": doc_id,
                    "source": source,
                    "total_chunks": total_chunks,
                },
            )

        except aiosqlite.Error:
            logger.exception("failed to insert document", extra={"doc_id": doc_id})
            raise

    async def read_from_cache(self) -> list:
        """Get all the rows from SQLite DB"""
        await self._ensure_connected()
        try:
            cursor = await self._db.execute("SELECT * FROM documents")
            rows = await cursor.fetchall()
            logger.debug("documents fetched", extra={"count": len(rows)})
            return rows

        except aiosqlite.Error:
            logger.exception("failed to read documents")
            raise
