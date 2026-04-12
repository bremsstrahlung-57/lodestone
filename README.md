# Lodestone

Lodestone is a local-first personal knowledge retrieval system that lets you store and search your documents semantically.

You can upload files, text, and bookmarks, and later retrieve them using natural language queries instead of filenames, folder paths, or exact keywords. Lodestone runs locally, keeps your data under your control, and optionally uses AI to generate answers grounded in your own documents.

It is designed to replace manual searching across folders, notes apps, and websites with a single searchable memory.

---

## **Current Version (v0.10.1)**
### What it does

- **Interactive React Frontend** — clean, responsive UI with dark/light mode, drag-and-drop file upload, and real-time settings management
- **Settings & API Key Management** — seamlessly switch between LLM providers and models, and add API keys directly from the UI
- **Expandable Search Results** — view full document texts and explore overlapping chunks right from the search results
- **Fully async backend** — end-to-end async across the API, database, embeddings, LLM clients, and retrieval pipeline
- **Async Qdrant client** — switched from `QdrantClient` to `AsyncQdrantClient` for non-blocking vector operations
- **Async SQLite via aiosqlite** — lazy-connected `aiosqlite` replaces the synchronous `sqlite3` driver with proper lifecycle management
- **Async LLM providers** — all four providers (Anthropic, OpenAI, Gemini, Groq) now use their native async clients (`AsyncAnthropic`, `AsyncOpenAI`, `AsyncGroq`, Gemini `aio`)
- **Thread-offloaded embeddings & cross-encoder** — CPU-bound sentence-transformer encoding and cross-encoder reranking run in `asyncio.to_thread` to avoid blocking the event loop
- **Async factory for Lodestone** — `Lodestone.create()` async classmethod replaces heavy work in `__init__`, keeping construction clean
- **Async test suite** — all tests converted to async with `pytest-asyncio` (`asyncio_mode = "auto"`)
- **Semantic search** over your own documents using sentence embeddings (MiniLM-L6-v2)
- **Two search modes** — plain retrieval or AI-answered with context from your docs
- **Multiple LLM providers** — Anthropic, OpenAI, Gemini and Groq, switchable per request
- **Chunking with overlap** — documents are split into overlapping chunks for better retrieval coverage
- **Chunk window expansion** — when a chunk matches, neighboring chunks are pulled in for fuller context
- **Score-based filtering** — results are ranked and filtered so you don't get garbage matches back
- **Document ingestion** — ingest files or raw text, automatically chunked, embedded, and stored
- **Qdrant vector DB** — all embeddings stored in Qdrant, runs locally via Docker
- **SQLite metadata store** — full document content and metadata cached locally via aiosqlite
- **Content-addressed doc IDs** — SHA3-256 hashing, same content = same ID, no duplicates
- **Structured logging** — rotating file logs across all layers (API, DB, LLM, ingestion, retrieval)
- **FastAPI backend** — single `/api/search` endpoint handles both retrieval and AI modes
- **CORS ready** — configured for local frontend on port 3000
- **Query rewriting** — rewrite query using ai for better search results
- **Cross Encoder Reranking** - uses cross encoder for cross encoder scoring
- **Normalized Scores** - ranks retrieved docs using cosine scores and normalized cross encoder scores

---
