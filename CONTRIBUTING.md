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
