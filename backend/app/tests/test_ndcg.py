import json
from math import log2
from statistics import mean, median

import pytest

from app.db.qdrant import search_docs


def load_ndcg_test_cases():
    with open("app/tests/test_cases/ndcg.json", "r") as f:
        data = json.load(f)
        return data["cases"]


@pytest.mark.parametrize("a", [i / 10.0 for i in range(0, 11)])
async def test_ndcg(a):
    ndcg_list = await ndcg(a)
    mean_ndcg = mean(ndcg_list)
    median_ndcg = median(ndcg_list)
    worst_ndcg = min(ndcg_list)

    print(f"alpha: {a}")
    print(f"mean_ndcg: {mean_ndcg}")
    print(f"median_ndcg: {median_ndcg}")
    print(f"worst_ndcg: {worst_ndcg}")

    assert mean_ndcg > 0.75
    assert median_ndcg > 0.80
    assert worst_ndcg > 0.3


async def ndcg(a):
    ndcg_l = []
    for case in load_ndcg_test_cases():
        query = case["query"]
        relevant_docs = case["relevant_docs"]
        limit = 50
        k = 10

        results = await search_docs(query=query, limit=limit, k=k, a=a)
        doc_ids = [item["doc_id"] for item in results]
        rankings = [item["rank"] for item in results]

        # print(f"Query: {query}")

        dcg = 0
        idcg = 0
        n = len(doc_ids)

        for doc_id, i in zip(doc_ids, rankings):
            rel_i = relevant_docs.get(doc_id, {}).get("relevance_grade", 0)
            dcg += ((2**rel_i) - 1) / log2(i + 1)

        ideal_relevances = sorted(
            [doc["relevance_grade"] for doc in relevant_docs.values()],
            reverse=True,
        )
        ideal_relevances.extend([0] * max(0, n - len(ideal_relevances)))

        for i, rel_i in enumerate(ideal_relevances[:n], start=1):
            idcg += ((2**rel_i) - 1) / log2(i + 1)

        ndcg = dcg / idcg if idcg > 0 else 0.0
        ndcg_l.append(ndcg)

        # print(f"ndcg: {ndcg}")
        # print(f"dcg: {dcg} | idcg: {idcg}")

    return ndcg_l
