import json

import pytest

from app.retrieval.docs_recall import Recall


def load_test_cases():
    with open("app/tests/recall_test.json", "r") as f:
        data = json.load(f)
        return data["test_cases"]


@pytest.mark.parametrize("case", load_test_cases(), ids=lambda c: c["test_id"])
def test_recall(case):
    test_id = case["test_id"]
    description = case["description"]
    input_data = case["input"]
    expected = case["expected"]

    print(f"\nTest: {test_id}")
    print(f"Description: {description}")

    result = Recall(
        query=input_data["query"],
        mode=input_data["mode"],
        limit=input_data["limit"],
        k=input_data["k"],
        provider=input_data["provider"],
    )

    assert result["mode"] == expected["mode"], (
        f"Mode mismatch: expected {expected['mode']}, got {result['mode']}"
    )

    assert result["query"] == input_data["query"], (
        f"Query mismatch: expected {input_data['query']}, got {result['query']}"
    )

    assert isinstance(result["results"], list), "Results should be a list"

    if expected.get("results_should_exist"):
        assert len(result["results"]) > 0, (
            "Expected results to exist but got empty list"
        )

    if "results_max_count" in expected:
        assert len(result["results"]) <= expected["results_max_count"], (
            f"Results count {len(result['results'])} exceeds max {expected['results_max_count']}"
        )

    if "result_fields" in expected:
        for res in result["results"]:
            for field in expected["result_fields"]:
                assert field in res, f"Missing field '{field}' in result"

    if expected.get("ai_answer_should_exist"):
        assert result["ai_answer"] is not None, "Expected AI answer to exist"
        assert isinstance(result["ai_answer"], str), "AI answer should be a string"
        assert len(result["ai_answer"]) > 0, "AI answer should not be empty"
    elif "ai_answer" in expected and expected["ai_answer"] is None:
        assert result["ai_answer"] is None, "Expected AI answer to be None"

    if expected.get("provider") is not None:
        assert result["provider"] == expected["provider"], (
            f"Provider mismatch: expected {expected['provider']}, got {result['provider']}"
        )
    elif "provider" in expected and expected["provider"] is None:
        assert result["provider"] is None, "Expected provider to be None"

    if expected.get("latency_ms_should_exist"):
        assert result["latency_ms"] is not None, "Expected latency_ms to exist"
        assert isinstance(result["latency_ms"], (int, float)), (
            "Latency should be numeric"
        )
        assert result["latency_ms"] > 0, "Latency should be positive"
    elif "latency_ms" in expected and expected["latency_ms"] is None:
        assert result["latency_ms"] is None, "Expected latency_ms to be None"

    if "llm_fields" in expected:
        assert "llm" in result, "Expected 'llm' key in result for AI mode"
        for field in expected["llm_fields"]:
            assert field in result["llm"], f"Missing LLM field '{field}'"

    if expected.get("llm_should_not_exist"):
        assert "llm" not in result, "Expected 'llm' key to not exist"

    print(f"Results count: {len(result['results'])}")
    if result["ai_answer"]:
        print(f"AI Answer: {result['ai_answer'][:100]}...")
    print("PASSED")


@pytest.mark.parametrize(
    "mode",
    ["retrieval", "ai"],
)
def test_recall_returns_correct_structure(mode):
    """Test that Recall returns the expected base structure"""
    provider = "groq" if mode == "ai" else None

    result = Recall(
        query="test query",
        mode=mode,
        limit=3,
        k=2,
        provider=provider,
    )

    assert "query" in result
    assert "mode" in result
    assert "results" in result
    assert "ai_answer" in result
    assert "provider" in result
    assert "latency_ms" in result


def test_recall_retrieval_mode_ignores_provider():
    """Test that retrieval mode works even when provider is given"""
    result = Recall(
        query="rpg games",
        mode="retrieval",
        limit=5,
        k=3,
        provider="gemini",
    )

    assert result["ai_answer"] is None
    assert result["provider"] is None
    assert result["latency_ms"] is None
    assert "llm" not in result
