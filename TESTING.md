## **Testing**

### Overview

Lodestone includes a deterministic test suite that validates retrieval quality, ranking logic, lodestone metrics, NDCG scoring, and prompt-injection handling.

All tests run against a fixed, canonical sample corpus located at:

```
app/scripts/samples/
```

This dataset is intentionally version-controlled to ensure reproducible results across environments and CI.

### Test Architecture

All tests are **async** and run under `pytest-asyncio` with `asyncio_mode = "auto"` (configured in `pyproject.toml`). No manual `@pytest.mark.asyncio` decorators are needed.

During test execution:

- A fresh Qdrant test collection is created.
- The sample documents are ingested automatically.
- Retrieval and evaluation tests are executed against this controlled corpus.
- The test collection is isolated from any user or production data.

### Test Modules

| Module | What it covers |
|---|---|
| `test_search.py` | Validates that semantic search returns expected documents for each query in `eval.json` |
| `test_lodestone.py` | End-to-end lodestone pipeline — response structure, retrieval/AI modes, query rewriting behaviour, and rewrite improvement over baseline |
| `test_ndcg.py` | Parametrised NDCG scoring across alpha values (0.0–1.0), asserts mean > 0.75, median > 0.80, worst > 0.3 |
| `test_prompt_injection.py` | Interactive prompt-injection resilience checks (requires manual pass/fail input) |

Test cases are defined in JSON files under `app/tests/test_cases/`:

- `eval.json` — query-to-expected-document mappings for search and rewrite tests
- `lodestone_test.json` — full lodestone pipeline test case definitions
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
pytest app/tests/test_lodestone.py -v
pytest app/tests/test_ndcg.py -v
```

The prompt injection tests require interactive input and should be run separately:

```
pytest app/tests/test_prompt_injection.py -v -s
```

> **Note:** Qdrant must be running locally on port 6333 before executing any tests. AI-mode and query-rewriting tests also require valid API keys in your `.env`. Check your rate limits for your API before running tests that calls them frequently. All test functions are async — `pytest-asyncio` handles event-loop creation automatically.

### Writing New Tests

- Add test cases to the relevant JSON file in `app/tests/test_cases/`, or create a new `test_*.py` module.
- Use the canonical sample corpus in `app/scripts/samples/` — do not add or modify sample files without discussion, as it affects all retrieval and ranking assertions.
- Use `pytest.mark.parametrize` for data-driven tests to keep things clean and extensible.
