# Recall

Recall is a local-first personal knowledge retrieval system that lets you store and search your documents semantically.

You can upload files, text, and bookmarks, and later retrieve them using natural language queries instead of filenames, folder paths, or exact keywords. Recall runs locally, keeps your data under your control, and optionally uses AI to generate answers grounded in your own documents.

It is designed to replace manual searching across folders, notes apps, and websites with a single searchable memory.

---

## **Current Version (v0.5.4)**
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
- **Cross Encoder Reranking** - uses cross encoder for cross encoder scoring
- **Normalized Scores** - ranks retrieved docs using cosine scores and normalized cross encoder scores

---

## **Contributing**

Contributions are welcome! Whether it's bug fixes, new features, documentation improvements, or test coverage — all help is appreciated.

### Getting Started

1. Fork the repository and clone your fork locally.
2. Make sure you have **Python 3.14+**, **Docker** (for Qdrant), and **uv** (or pip) available.
3. Install dependencies from the backend directory:
   ```
   cd backend
   uv sync
   ```
4. Copy `.env.example` to `.env` and fill in any required API keys (Gemini, Groq) if you plan to run AI-mode or query-rewriting tests.
5. Start Qdrant locally via Docker:
   ```
   docker run -p 6333:6333 qdrant/qdrant
   ```

### Making Changes

- Create a feature branch from `master`.
- Keep commits focused — one logical change per commit.
- Follow the existing code style. The project uses **Ruff** for linting and **Pyright** for type checking.
- If you add a new feature, add corresponding tests under `app/tests/`.

---

## **Testing**

### Overview

Recall includes a deterministic test suite that validates retrieval quality, ranking logic, recall metrics, NDCG scoring, and prompt-injection handling.

All tests run against a fixed, canonical sample corpus located at:

```
app/debug/samples/
```

This dataset is intentionally version-controlled to ensure reproducible results across environments and CI.

### Test Architecture

During test execution:

- A fresh Qdrant test collection is created.
- The sample documents are ingested automatically.
- Retrieval and evaluation tests are executed against this controlled corpus.
- The test collection is isolated from any user or production data.

### Test Modules

| Module | What it covers |
|---|---|
| `test_search.py` | Validates that semantic search returns expected documents for each query in `eval.json` |
| `test_recall.py` | End-to-end recall pipeline — response structure, retrieval/AI modes, query rewriting behaviour, and rewrite improvement over baseline |
| `test_ndcg.py` | Parametrised NDCG scoring across alpha values (0.0–1.0), asserts mean > 0.75, median > 0.80, worst > 0.3 |
| `test_prompt_injection.py` | Interactive prompt-injection resilience checks (requires manual pass/fail input) |

Test cases are defined in JSON files under `app/tests/test_cases/`:

- `eval.json` — query-to-expected-document mappings for search and rewrite tests
- `recall_test.json` — full recall pipeline test case definitions
- `ndcg.json` — queries with relevance-graded document mappings for NDCG evaluation
- `prompt_injection_test.json` — adversarial prompt injection payloads

### Running Tests

From the `backend/` directory, run the full automated suite:

```
pytest app/tests/ -v
```

Run a specific test module:

```
pytest app/tests/test_search.py -v
pytest app/tests/test_recall.py -v
pytest app/tests/test_ndcg.py -v
```

The prompt injection tests require interactive input and should be run separately:

```
pytest app/tests/test_prompt_injection.py -v -s
```

> **Note:** Qdrant must be running locally on port 6333 before executing any tests. AI-mode and query-rewriting tests also require valid API keys in your `.env`. Check your rate limits for your API before running tests that calls them frequently.

### Writing New Tests

- Add test cases to the relevant JSON file in `app/tests/test_cases/`, or create a new `test_*.py` module.
- Use the canonical sample corpus in `app/debug/samples/` — do not add or modify sample files without discussion, as it affects all retrieval and ranking assertions.
- Use `pytest.mark.parametrize` for data-driven tests to keep things clean and extensible.
