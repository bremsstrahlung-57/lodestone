## **Contributing**

Contributions are welcome! Whether it's bug fixes, new features, documentation improvements, or test coverage — all help is appreciated.

> **Note:** The backend is fully async — all database access, embedding, LLM calls, and retrieval use `async`/`await`. New code should follow the same pattern.

### Getting Started

1. Fork the repository and clone your fork locally.
2. Make sure you have **Node.js** (for frontend), **Python 3.12+**, **Docker** (for Qdrant), and **uv** (or pip) available.
3. Install dependencies from the backend directory:
   ```
   cd backend
   uv sync
   ```
4. Copy `.env.example` to `.env` and fill in any required API keys (Gemini, Groq) if you plan to run AI-mode or query-rewriting tests.
5. Start Qdrant locally via Docker:
   ```
   docker run -p 8092:6333 qdrant/qdrant
   ```
6. Start the frontend development server:
   ```
   cd frontend
   npm install
   npm run dev
   ```

### Making Changes

- Create a feature branch from `master`.
- Keep commits focused — one logical change per commit.
- Follow the existing code style. The project uses **Ruff** for linting and **Pyright** for type checking on the backend, and **ESLint** on the frontend.
- All backend code is **async**. Use `async def` for any function that touches the database, Qdrant, embeddings, or LLM clients. For CPU-bound work (e.g. sentence-transformer encoding, cross-encoder), wrap with `asyncio.to_thread`.
- Tests use `pytest-asyncio` with `asyncio_mode = "auto"` — write test functions as `async def` and they will be picked up automatically (no `@pytest.mark.asyncio` needed).
- If you add a new feature, add corresponding tests under `app/tests/`.
- Frontend changes should be tested against both Light and Dark mode to ensure UI consistency. Keep custom CSS in `App.css` or `index.css` using CSS variables.
