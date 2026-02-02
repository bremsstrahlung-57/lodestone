import json

import pytest

from app.db.qdrant import search_docs


def load_cases():
    with open("app/tests/eval.json", "r") as f:
        return json.load(f)


@pytest.mark.parametrize("case", load_cases())
def test_search_docs(case):
    query = case["query"]
    expected = set(case["expected"])
    limit = 5

    results = search_docs(query, limit)
    found_ids = {res["doc_id"] for res in results}

    print(f"\nQuery   : {query}")
    print(f"Expected: {expected}")

    for doc_id in found_ids:
        if doc_id in expected:
            print(f"Found   : {doc_id[:10]}...")

    assert expected & found_ids, (
        f"No expected documents found for query '{query}'. Found: {found_ids}"
    )
