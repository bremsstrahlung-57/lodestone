import logging
import os
import sqlite3
from datetime import datetime

from app.core.constants import DATA_FILE_PATH, DATA_PATH

logger = logging.getLogger(__name__)


def make_cache_folder():
    """Create cache/ folder if doesn't exists already"""
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
    """All functions related to SQLite Database storing user docs and all other important metadata"""

    def __init__(self) -> None:
        logger.info("initializing SQLite database")

        make_cache_folder()

        try:
            self.connection = sqlite3.connect(DATA_FILE_PATH, check_same_thread=False)
            logger.info("database connected", extra={"db": DATA_FILE_PATH})
        except sqlite3.Error:
            logger.exception("failed to connect to database")
            raise

        self.connection.execute("""
        CREATE TABLE IF NOT EXISTS documents (
        doc_id TEXT PRIMARY KEY,
        title TEXT,
        content TEXT NOT NULL,
        source TEXT,
        total_chunks INTEGER,
        created_at TEXT
        );""")
        self.connection.commit()

        logger.debug("documents table ensured")

    def insert_doc_ib_db(
        self,
        doc_id: str,
        title: str,
        content: str,
        source: str,
        total_chunks: int,
    ) -> None:
        """Save full doc and other metadata in the SQLite DB"""
        make_cache_folder()
        iso_format = iso_format = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            self.connection.execute(
                """
        INSERT OR REPLACE INTO documents (doc_id, title, content, source, total_chunks, created_at)
        VALUES(?, ?, ?, ?, ?, ?)
        """,
                (doc_id, title, content, source, total_chunks, iso_format),
            )
            self.connection.commit()

            logger.info(
                "document saved",
                extra={
                    "doc_id": doc_id,
                    "source": source,
                    "total_chunks": total_chunks,
                },
            )

        except sqlite3.Error:
            logger.exception("failed to insert document", extra={"doc_id": doc_id})
            raise

    def read_from_cache(self) -> list:
        """Get all the rows from SQLite DB"""
        try:
            cursor = self.connection.execute("SELECT * FROM documents")
            rows = cursor.fetchall()
            logger.debug("documents fetched", extra={"count": len(rows)})
            return rows
        except sqlite3.Error:
            logger.exception("failed to read documents")
            raise
