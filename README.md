<div align="center">

<h1>Lodestone</h1>

![Version](https://img.shields.io/badge/version-0.10.2-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-active-brightgreen)
![GitHub stars](https://img.shields.io/github/stars/bremsstrahlung-57/lodestone)
![Last commit](https://img.shields.io/github/last-commit/bremsstrahlung-57/lodestone)

<p>Lodestone is a local-first document retrieval system. Drop in files, then search them with natural language instead of filenames, folder structures, or exact keywords. Lodestone runs entirely on your machine, keeps your data local, and can optionally use an LLM to generate answers grounded in your documents.</p>

https://github.com/user-attachments/assets/c197bb8a-7c3d-4574-ba9f-ebc9ad48db85

</div>

---

## Features

- Semantic search over your own documents using sentence embeddings
- AI-answered queries with retrieved context as grounding
- Drag-and-drop file ingestion from the browser
- Full document viewer with expandable neighboring chunks
- Switchable LLM providers: Anthropic, OpenAI, Gemini, Groq
- Dark/light theme, persistent settings, API key management from the UI
- Content-addressed deduplication via SHA3-256

---

## How It Works

Ingested documents are chunked, embedded with MiniLM-L6-v2, and stored in a local Qdrant instance. Queries go through optional AI rewriting, dense vector search, cross-encoder reranking, and score-based filtering before results are returned. Full document content is cached in SQLite. Everything is async end-to-end.

---

## Stack

| Layer | Technology |
|---|---|
| Frontend | React + Vite |
| Backend | FastAPI |
| Vector store | Qdrant (local via Docker) |
| Metadata store | SQLite via aiosqlite |
| Embeddings | MiniLM-L6-v2 |
| Reranking | Cross-encoder |
| LLM providers | Anthropic, OpenAI, Gemini, Groq |

---

## Quickstart

**Prerequisites**: Python 3.10+, Node.js, Docker

```bash
# Start Qdrant
docker run -p 6333:6333 qdrant/qdrant

# Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. Add your API key in Settings, drop in a file, and search.

---

## Configuration

Lodestone follows the XDG base directory spec. On first run, config files are created at:

- `~/.config/lodestone/config.toml` — general settings and defaults
- `~/.config/lodestone/keys.toml` — API keys, gitignored by default

---

## Status

Active development. v0.10.2.
