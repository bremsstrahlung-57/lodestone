# Recall

Recall is a local-first personal knowledge retrieval system that lets you store and search your documents semantically.

You can upload files, text, and bookmarks, and later retrieve them using natural language queries instead of filenames, folder paths, or exact keywords. Recall runs locally, keeps your data under your control, and optionally uses AI to generate answers grounded in your own documents.

It is designed to replace manual searching across folders, notes apps, and websites with a single searchable memory.

## Current Version (v0.4.2)
### What it does

- **Semantic search** over your own documents using sentence embeddings (MiniLM-L6-v2)
- **Two search modes** — plain retrieval or AI-answered with context from your docs
- **Multiple LLM providers** — Gemini and Groq (LLaMA), switchable per request
- **Chunking with overlap** — documents are split into overlapping chunks for better retrieval coverage
- **Chunk window expansion** — when a chunk matches, neighboring chunks are pulled in for fuller context
- **Score-based filtering** — results are ranked and filtered so you don't get garbage matches back
- **Document ingestion** — ingest files or raw text, automatically chunked, embedded, and stored
- **Qdrant vector DB** — all embeddings stored in Qdrant, runs locally via Docker
- **SQLite metadata store** — full document content and metadata cached locally
- **Content-addressed doc IDs** — SHA3-256 hashing, same content = same ID, no duplicates
- **Structured logging** — rotating file logs across all layers (API, DB, LLM, ingestion, retrieval)
- **FastAPI backend** — single `/api/search` endpoint handles both retrieval and AI modes
- **CORS ready** — configured for local frontend on port 3000
- **Query rewriting** — rewrite query using ai for better search results
