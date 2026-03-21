import json

import pytest
from app.retrieval.docs_lodestone import Lodestone


def load_prompt_injection_test_json_cases():
    with open("app/tests/test_cases/prompt_injection_test.json", "r") as f:
        data = json.load(f)
        return data["cases"]


@pytest.mark.parametrize("case", load_prompt_injection_test_json_cases())
@pytest.mark.parametrize("rewrite_query", [True, False])
async def test_prompt_injection(case, rewrite_query):
    query = case["prompt"]
    limit = 5
    k = 3
    mode = "ai"
    provider = "groq"

    t = await Lodestone.create(
        request_id="test_prompt_injection",
        query=query,
        limit=limit,
        k=k,
        mode=mode,
        provider=provider,
        rewrite_query=rewrite_query,
    )
    r = await t.get_results()
    print(f"Query: {query}")
    if rewrite_query:
        print(f"Rewritten Query:{r['retrieval']['rewritten_query']}")
    print(f"AI Ans:{r['ai_response']['ai_answer']}\n")

    is_this_correct = input("Passed the test?(y/n): ").lower()
    if is_this_correct == "":
        is_this_correct = "y"

    assert is_this_correct == "y"
