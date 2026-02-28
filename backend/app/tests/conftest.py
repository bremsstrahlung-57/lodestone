import pytest

from app.db.qdrant import _doc_database


@pytest.fixture(autouse=True, scope="session")
async def setup_sqlite():
    """Ensure the SQLite connection is open for the entire test session."""
    await _doc_database.connect()
    yield
    await _doc_database.close()
