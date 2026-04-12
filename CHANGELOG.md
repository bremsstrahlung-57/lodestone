# Changelog

All notable changes to **Lodestone** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [0.10.1] - 2026-04-12
### Added
- **Frontend MVP**: Fully functional React/Vite web interface with dark/light mode, CSS animations, and responsive design.
- **Drag-and-Drop Ingestion**: File drag-and-drop support in the UI, backed by a new `/ingest` endpoint using secure temporary directories.
- **Full Document Viewer**: Modal view for complete document text, backed by a new `/document/{doc_id}` endpoint.
- **Context Expansion**: UI support for viewing neighboring chunks around any retrieved document.
- **CLI Batch Ingestion**: `ingest-samples` command in `cli.py` for ingesting a directory of sample files in one shot.
- **Toast Notifications**: `react-hot-toast` integration with theme-aware styling.

### Changed
- Rebuilt the React app into a full semantic search and chat interface: added query/result routing, chat state management, and document viewer components.
- SQLite queries now fetch document content via `doc_id` rather than title.

### Fixed
- `docs_lodestone.py` was returning the original query in results instead of the AI-rewritten query.
- `SQLiteDB.get_whole_file_data` was improperly awaiting cursor execution, causing fetch errors.
- UI chunk rendering was crashing due to Qdrant object dictionaries being parsed instead of raw strings.

---

## [0.9.1] - 2026-04-11
### Added
- `APIDefaultAIRequest` schema and `save_default_model` handler with a `/add_default_model` POST endpoint to persist provider and model defaults.
- Settings UI for provider/model selection, default saving, API key input, and theme persistence.

### Changed
- Lodestone now falls back to configured defaults when provider is omitted from a request.
- `rewritten_query` is now exposed in retrieval results.

### Fixed
- Incorrect `DEFAULT_GOOGLE_API_KEY` naming in the LLM factory.

---

## [0.9.0] - 2026-04-07
### Added
- App config now loads LLM defaults and API keys on startup.

### Changed
- Renamed Gemini provider to Google across config, LLM factory, CLI, tests, and fixtures.

### Removed
- `backend/.env.example`.

---

## [0.8.0] - 2026-03-21

### Added
- Updated documentation (README, TESTING) and test metadata for the new project name.

### Changed
- Renamed project and package from `recall` to `lodestone`.
- Bumped version to `0.8.0` in `pyproject.toml` and updated `uv.lock`.
- Renamed core retrieval module `docs_recall.py` to `docs_lodestone.py` and class to `Lodestone`.
- Renamed CLI class and commands from `RecallCLI`/`recall` to `LodestoneCLI`/`lodestone`.
- Updated `backend/app/api/endpoints.py` to use `Lodestone` and set `APP_VERSION` to package `lodestone`.
- Modified API key extraction in `backend/app/llm/factory.py` to use `.get_secret_value()` on settings secrets.
- Relocated embedding constants (`EMBEDDING_MODEL` / `EMBEDDING_DIM`) in `qdrant.py` and `minilm.py`.
- Updated test files and references (renamed `test_recall.py` to `test_lodestone.py`).
- Simplified `LLMFactory` and `LLMGeneration` to use global defaults, removing per-call `api_key` and `model` arguments.

### Removed
- Removed the CLI provider helper `llm_provider` from `backend/app/llm/generation.py`.

---

## [0.7.0] - 2026-02-28

### Added

- Full async/await support across the entire backend (API, database, embeddings, LLM clients, retrieval, ingestion, CLI).
- `AsyncQdrantClient` replacing the synchronous `QdrantClient` for non-blocking vector operations.
- `aiosqlite` dependency for async SQLite access, replacing synchronous `sqlite3`.
- Lazy async connection management for SQLite with `connect()` / `close()` lifecycle methods.
- `Recall.create()` async classmethod factory for async-safe initialization (query rewriting, search).
- `asyncio.to_thread` wrappers for CPU-bound sentence-transformer embedding and cross-encoder reranking.
- `cross_encode()` async helper in `qdrant.py` for thread-offloaded cross-encoder prediction.
- `pytest-asyncio` dependency with `asyncio_mode = "auto"` for async test execution.
- SQLite connection startup/shutdown hooks in the FastAPI lifespan.
- `_run()` async entry point in CLI with proper database cleanup on exit.

### Changed

- Converted all API endpoint handlers (`health_check`, `search_api`) to async.
- Converted all Qdrant operations (`ping_qdrant`, `_assert_embedding_dim`, `ensure_collection_exists`, `search_docs`, `ingest_data`, `fetch_chunk_by_ids`) to async.
- Converted `SQLiteDB` methods (`insert_doc_ib_db`, `read_from_cache`) to async with `_ensure_connected()` guard.
- Converted `embed()` to async wrapper around `_embed_sync()` via `asyncio.to_thread`.
- Converted all LLM provider classes (`GeminiLLM`, `GroqLLM`, `OpenAILLM`, `AnthropicLLM`) to use native async clients (`AsyncAnthropic`, `AsyncOpenAI`, `AsyncGroq`, Gemini `aio`) with async `generate()` and `query_rewrite()` methods.
- Converted `LLMGeneration.generate()` and `LLMGeneration.rewrite_query()` to async.
- Converted `Recall.get_results()` and `Recall.ai_result()` to async.
- Converted `build_context()` in retrieval to async.
- Converted ingestion functions (`ingest_file`, `ingest_text`) to async with explicit connection lifecycle.
- Converted all CLI handlers and `RecallCLI` methods to async; CLI main uses `asyncio.run()`.
- Converted all test functions (`test_search`, `test_recall`, `test_ndcg`, `test_prompt_injection`) to async.
- Switched from `Recall(...)` constructor to `await Recall.create(...)` across all call sites.
- Fixed query rewrite null-check expressions (`if not None` → `if response.text`) in Gemini, Groq, and OpenAI clients.

### Removed

- Synchronous `create_gemini_client`, `create_groq_client`, `create_openai_client`, `create_anthropic_client` factory functions from LLM client module.
- `generate_context` CLI subcommand and `generate_llm_context` method (redundant with `build_llm_context`).

---

## [0.6.4] - 2026-02-23

### Added

- OpenAI and Anthropic as LLM providers for AI response generation and query rewriting, alongside existing Gemini and Groq support.
- `OpenAILLM` and `AnthropicLLM` client classes with `generate()` and `query_rewrite()` methods.
- Structured error handling for all LLM providers; AI responses now include `error_code`, `error`, and `status` fields on failure.
- `anthropic` and `openai` Python dependencies.
- Full CLI tool (`app/scripts/cli.py`) using `argparse` with subcommands: `ingest`, `search`, `context`, `prompt`, `generate`, `recall`.
- OpenAI and Anthropic API key and model settings in `.env.example` and `Settings`.

### Changed

- Renamed `app/debug/` to `app/scripts/`; refactored `cli.py` from ad-hoc debug script into a structured CLI tool.
- LLM `generate()` methods now return `LLMResponse` directly with error fields instead of raising on failure.
- `docs_recall` `ai_result()` now propagates LLM error data (`error_code`, `error`, `status`) into the `ai_response` result.
- Improved system prompt with explicit start/end markers and stronger anti-injection rules.
- Bumped version from 0.5.4 to 0.6.4.
- Updated README, TESTING docs, and `.env.example`.

### Removed

- `app/debug/cli.py` (replaced by `app/scripts/cli.py`).
- `parse_response()` abstract method from `BaseLLM` (response parsing now handled inline in `generate()`).

---

## [0.5.4] - 2026-02-19

### Added

- Request ID propagation through API and Recall; return `X-Request-ID` and `X-Response-Time` headers.
- Total latency tracking in response metadata.

### Changed

- Restructured response format from Recall.
- Standardized LLM latency field to `response_latency_ms` and updated logs.
- Set API `limit` parameter minimum to 5.
- Updated README.md, CONTRIBUTING.md and TESTING.md with improved documentation.
- Updated tests to match new return structure and improved error handling in API calls.

---

## [0.4.4] - 2026-02-18

### Added

- NDCG test and test data (`ndcg.json`).
- Test cases for query rewriting improvement over base retrieval.
- Manual tests for prompt injection prevention (`prompt_injection_test.json`).

### Changed

- Improved prompts for preventing prompt injection.
- Optimized cross-encoder for faster speeds on GPU.
- Reorganized test cases into `test_cases/` subdirectory.
- Removed upper limit for `limit` and `k` values in API.
- Renamed `vector_roundtrip.py` to `cli.py`.

---

## [0.4.3] - 2026-02-15

### Added

- Cross-encoder reranking using `cross-encoder/ms-marco-TinyBERT-L2-v2`.
- Normalized scoring combining cosine similarity and cross-encoder scores.

### Changed

- Replaced `filter_qdrant_results` with `filter_results` using normalized scores.
- Updated retrieval pipeline to incorporate cross-encoder reranking.

### Removed

- `refine_results` function.
- Unused functions from retrieval module.

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
