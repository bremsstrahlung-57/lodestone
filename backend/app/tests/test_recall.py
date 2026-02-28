import json

import pytest

from app.retrieval.docs_recall import Recall


def load_test_cases():
    with open("app/tests/test_cases/recall_test.json", "r") as f:
        data = json.load(f)
        return data["test_cases"]


def load_eval_json_test_cases():
    with open("app/tests/test_cases/eval.json", "r") as f:
        return json.load(f)


@pytest.mark.parametrize("case", load_test_cases(), ids=lambda c: c["test_id"])
async def test_recall(case):
    test_id = case["test_id"]
    description = case["description"]
    input_data = case["input"]
    expected = case["expected"]

    print(f"\nTest: {test_id}")
    print(f"Description: {description}")

    rec = await Recall.create(
        request_id="test_recall",
        query=input_data["query"],
        mode=input_data["mode"],
        limit=input_data["limit"],
        k=input_data["k"],
        provider=input_data["provider"],
        rewrite_query=input_data.get("rewrite_query", False),
    )
    result = await rec.get_results()

    assert result["retrieval"]["mode"] == expected["mode"], (
        f"Mode mismatch: expected {expected['mode']}, got {result['retrieval']['mode']}"
    )

    assert result["retrieval"]["query"] == input_data["query"], (
        f"Query mismatch: expected {input_data['query']}, got {result['retrieval']['query']}"
    )

    assert isinstance(result["retrieval"]["results"], list), "Results should be a list"

    if expected.get("results_should_exist"):
        assert len(result["retrieval"]["results"]) > 0, (
            "Expected results to exist but got empty list"
        )

    if "results_max_count" in expected:
        assert len(result["retrieval"]["results"]) <= expected["results_max_count"], (
            f"Results count {len(result['retrieval']['results'])} exceeds max {expected['results_max_count']}"
        )

    if "result_fields" in expected:
        for res in result["retrieval"]["results"]:
            for field in expected["result_fields"]:
                assert field in res, f"Missing field '{field}' in result"

    if expected.get("ai_answer_should_exist"):
        assert result["ai_response"]["ai_answer"] is not None, (
            "Expected AI answer to exist"
        )
        assert isinstance(result["ai_response"]["ai_answer"], str), (
            "AI answer should be a string"
        )
        assert len(result["ai_response"]["ai_answer"]) > 0, (
            "AI answer should not be empty"
        )
    elif "ai_answer" in expected and expected["ai_answer"] is None:
        assert result["ai_response"]["ai_answer"] is None, (
            "Expected AI answer to be None"
        )

    if expected.get("provider") is not None:
        assert result["ai_response"]["provider"] == expected["provider"], (
            f"Provider mismatch: expected {expected['provider']}, got {result['ai_response']['provider']}"
        )
    elif "provider" in expected and expected["provider"] is None:
        assert result["ai_response"]["provider"] is None, "Expected provider to be None"

    if expected.get("latency_ms_should_exist"):
        assert result["meta"]["total_latency_ms"] is not None, (
            "Expected total_latency_ms to exist"
        )
        assert isinstance(result["meta"]["total_latency_ms"], (int, float)), (
            "Latency should be numeric"
        )
        assert result["meta"]["total_latency_ms"] > 0, "Latency should be positive"
    elif "latency_ms" in expected and expected["latency_ms"] is None:
        assert result["ai_response"]["response_latency_ms"] == 0.0, (
            "Expected response_latency_ms to be 0.0"
        )

    if "llm_fields" in expected:
        assert "llm" in result["ai_response"], (
            "Expected 'llm' key in ai_response for AI mode"
        )
        for field in expected["llm_fields"]:
            assert field in result["ai_response"]["llm"], f"Missing LLM field '{field}'"

    if expected.get("llm_should_not_exist"):
        assert "llm" not in result["ai_response"], (
            "Expected 'llm' key to not exist in ai_response"
        )

    # Query rewriting assertions
    if expected.get("rewritten_query_should_equal_query"):
        assert result["retrieval"]["rewritten_query"] == input_data["query"], (
            f"Expected rewritten_query to equal original query '{input_data['query']}', "
            f"got '{result['retrieval']['rewritten_query']}'"
        )

    if expected.get("rewritten_query_should_differ"):
        assert result["retrieval"]["rewritten_query"] != input_data["query"], (
            f"Expected rewritten_query to differ from original query '{input_data['query']}', "
            f"but they are the same"
        )

    if expected.get("rewritten_query_should_not_be_empty"):
        assert result["retrieval"]["rewritten_query"] is not None, (
            "Rewritten query should not be None"
        )
        assert len(result["retrieval"]["rewritten_query"].strip()) > 0, (
            "Rewritten query should not be empty"
        )

    print(f"Results count: {len(result['retrieval']['results'])}")
    print(f"Rewritten query: {result['retrieval']['rewritten_query']}")
    if result["ai_response"]["ai_answer"]:
        print(f"AI Answer: {result['ai_response']['ai_answer'][:100]}...")
    print("PASSED")


@pytest.mark.parametrize(
    "mode",
    ["retrieval", "ai"],
)
async def test_recall_returns_correct_structure(mode):
    """Test that Recall returns the expected base structure"""
    provider = "groq" if mode == "ai" else None

    rec = await Recall.create(
        request_id="test_recall_returns_correct_structure",
        query="test query",
        mode=mode,
        limit=3,
        k=2,
        provider=provider,
        rewrite_query=False,
    )
    result = await rec.get_results()

    assert "retrieval" in result
    assert "ai_response" in result
    assert "meta" in result
    assert "query" in result["retrieval"]
    assert "mode" in result["retrieval"]
    assert "results" in result["retrieval"]
    assert "rewritten_query" in result["retrieval"]
    assert "retrieval_latency_ms" in result["retrieval"]
    assert "ai_answer" in result["ai_response"]
    assert "provider" in result["ai_response"]
    assert "response_latency_ms" in result["ai_response"]
    assert "request_id" in result["meta"]
    assert "total_latency_ms" in result["meta"]


async def test_recall_retrieval_mode_ignores_provider():
    """Test that retrieval mode works even when provider is given"""
    rec = await Recall.create(
        request_id="test_recall_retrieval_mode_ignores_provider",
        query="rpg games",
        mode="retrieval",
        limit=5,
        k=3,
        provider="gemini",
        rewrite_query=False,
    )
    result = await rec.get_results()

    assert result["ai_response"]["ai_answer"] is None
    assert result["ai_response"]["provider"] is None
    assert result["ai_response"]["response_latency_ms"] == 0.0
    assert "llm" not in result["ai_response"]


async def test_rewrite_query_disabled_returns_original():
    """When rewrite_query=False, rewritten_query should be the same as user query"""
    query = "kratos from which game"
    rec = await Recall.create(
        request_id="test_rewrite_query_disabled_returns_original",
        query=query,
        mode="retrieval",
        limit=3,
        k=2,
        provider=None,
        rewrite_query=False,
    )
    result = await rec.get_results()

    assert result["retrieval"]["rewritten_query"] == query


async def test_rewrite_query_no_provider_falls_back():
    """When rewrite_query=True but provider=None, should fall back to original query"""
    query = "eldenring plot pls"
    rec = await Recall.create(
        request_id="test_rewrite_query_no_provider_falls_back",
        query=query,
        mode="retrieval",
        limit=3,
        k=2,
        provider=None,
        rewrite_query=True,
    )
    result = await rec.get_results()

    assert result["retrieval"]["rewritten_query"] == query


@pytest.mark.parametrize("provider", ["gemini", "groq"])
async def test_rewrite_query_produces_different_query(provider):
    """When rewrite_query=True with a provider, the rewritten query should differ from the original"""
    query = "eldenring plot pls"
    rec = await Recall.create(
        request_id="test_rewrite_query_produces_different_query",
        query=query,
        mode="retrieval",
        limit=3,
        k=2,
        provider=provider,
        rewrite_query=True,
    )
    result = await rec.get_results()

    assert result["retrieval"]["rewritten_query"] is not None
    assert len(result["retrieval"]["rewritten_query"].strip()) > 0, (
        "Rewritten query should not be empty"
    )
    assert result["retrieval"]["rewritten_query"] != query, (
        f"Expected rewritten query to differ from '{query}', got '{result['retrieval']['rewritten_query']}'"
    )


@pytest.mark.parametrize("provider", ["gemini", "groq"])
async def test_rewrite_query_preserves_question_intent(provider):
    """A question query should remain a question after rewriting, not become a label/description"""
    query = "kratos from which game"
    rec = await Recall.create(
        request_id="test_rewrite_query_preserves_question_intent",
        query=query,
        mode="retrieval",
        limit=3,
        k=2,
        provider=provider,
        rewrite_query=True,
    )
    result = await rec.get_results()

    rewritten = result["retrieval"]["rewritten_query"]
    assert rewritten is not None
    assert len(rewritten.strip()) > 0

    intent_markers = ["which", "what", "from", "?", "game"]
    has_intent = any(marker in rewritten.lower() for marker in intent_markers)
    assert has_intent, (
        f"Rewritten query '{rewritten}' lost the question intent of original query '{query}'. "
        f"Expected at least one of {intent_markers} to be present."
    )


async def test_rewrite_query_clear_query_minimal_change():
    """A query that is already clear should be returned with minimal changes"""
    query = "What is the main character in God of War?"
    rec = await Recall.create(
        request_id="test_rewrite_query_clear_query_minimal_change",
        query=query,
        mode="retrieval",
        limit=3,
        k=2,
        provider="gemini",
        rewrite_query=True,
    )
    result = await rec.get_results()

    rewritten = result["retrieval"]["rewritten_query"]
    assert rewritten is not None

    key_terms = ["god of war", "main character"]
    for term in key_terms:
        assert term in rewritten.lower(), (
            f"Rewritten query '{rewritten}' lost key term '{term}' from original '{query}'"
        )


@pytest.mark.parametrize("case", load_eval_json_test_cases())
async def test_rewrite_improvement(case):
    """Test if rewritten query actually gives better results"""

    query = case["query"]
    expected_ids = set(case["expected"])
    limit = 5
    k = 3
    provider = "groq"

    baseline_rec = await Recall.create(
        request_id="test_rewrite_improvement_baseline",
        query=query,
        mode="retrieval",
        limit=limit,
        k=k,
        provider=provider,
        rewrite_query=False,
    )
    baseline = await baseline_rec.get_results()

    rewritten_rec = await Recall.create(
        request_id="test_rewrite_improvement_rewritten",
        query=query,
        mode="retrieval",
        limit=limit,
        k=k,
        provider=provider,
        rewrite_query=True,
    )
    rewritten = await rewritten_rec.get_results()

    baseline_ids = {doc["doc_id"] for doc in baseline["retrieval"]["results"]}
    rewritten_ids = {doc["doc_id"] for doc in rewritten["retrieval"]["results"]}

    assert len(rewritten_ids & expected_ids) >= len(baseline_ids & expected_ids), (
        f"Query: {query} | Rewritten: {rewritten['retrieval']['rewritten_query']}"
    )
