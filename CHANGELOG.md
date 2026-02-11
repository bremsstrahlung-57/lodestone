# Changelog

All notable changes to **Recall** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [0.4.2] - 2026-02-11

### Added

- Query rewriting in the Recall class to improve search relevance
- Unit tests for query rewriting
- `filter_qdrant_results` for enhanced Qdrant search result filtering

### Changed

- Refactored Recall from a function to a class
- Improved overall search result filtering logic

---

## [0.3.2] — 2026-02-08

### Added

- Logging across the application.
- Unit tests for the Recall function.
- LLM response metadata in Recall function.
- Universal function to get full document text, AI answer, or both.

### Changed

- Improved the Recall function and removed the previous implementation.
- Added `/api` prefix to all endpoints.

### Fixed

- Bugs in SQLite layer.

---

## [0.3.1] — 2026-01-28

### Added

- LLM client abstraction layer.
- `llm_context_builder` function for LLM-powered answering.
- Search endpoint with retrieval function for context building.
- Functions for context building in retrieval pipeline.
- `k` parameter for search and deterministic point IDs.
- Score field in `refine_results`.
- Title field in SQLite database.
- Metadata in `search_docs` in `qdrant.py`.

### Changed

- Rebuild RAG retrieval pipeline with doc-aware chunk aggregation.
- Accept list-based context from overlapping chunks and proceed without cleanup.
- Return deduplicated list of chunk texts from `build_context` instead of a single joined string.
- Refactored `vector_roundtrip.py` — extract ingest routine, add ds3 sample, and simplify debug output.
- Renamed `health.py` to `endpoints.py`.
- Reset SQLite and Qdrant schema for new chunk aggregation model.
- Preserve top-k chunks per document.

### Fixed

- SQLite thread error while calling search endpoint (`check_same_thread=False`).
- Removed duplicate lines of code in `test_db.py`.

---

## [0.2.1] — 2026-01-24

### Added

- `pytest` as a dev dependency with `tests/eval.json` and `tests/test_db.py`.
- DB search tests for `search_docs`.

### Changed

- Renamed `search_chunks` to `search_docs` and updated debug imports.
- Tightened result filtering to require score ≥ 0.25 and ≥ 60% of the max score.
- Aggregated chunk scores per document — store `all_scores` and `max_score`; compute mean, median, mode, and top-3 average.
- Use top-3 average as the result score; discard results with score ≤ 0.35.
- Updated README example output and stats.

---

## [0.2.0] — 2026-01-18

### Added

- SQLite caching layer (`SQLiteDB` class) to persist document content, source, and chunk info.
- Enhanced `search_chunks` to return full document details by joining vector results with cached metadata.
- Docstrings across modules (`qdrant`, `minilm`, `chunking`, `doc_id`).
- `.gitignore` entries for `cache/` directory and `.txt` files.
- `vector_roundtrip` sample output in README.

### Changed

- Renamed project from `backend` to `recall`.
- Renamed `ingest_file.py` to `ingestion.py` with support for both file and text ingestion.
- Refactored ingestion to store documents in SQLite before vector indexing.

---

## [0.1.0] — 2026-01-14

### Added

- Initial project setup with FastAPI backend and Next.js frontend.
- Structured app layout, config system, and health router.
- Qdrant connection and collection initialization with MiniLM embeddings.
- Qdrant ingest, search, and debug utilities.
