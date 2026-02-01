from app.db.qdrant import search_docs
from app.llm.generation import LLMGeneration, prompt_generation
from app.retrieval.retrieve import refine_results


def Recall(
    query: str,
    mode: str,
    limit: int,
    k: int,
    provider: str | None,
):
    RESULT = {
        "query": query,
        "mode": mode,
        "results": [],
        "ai_answer": None,
        "provider": None,
        "latency_ms": None,
    }

    call_llm = LLMGeneration()
    searched_docs = search_docs(query=query, limit=limit, k=k)
    refined_docs = refine_results(searched_docs)

    for docs in searched_docs:
        doc_id = docs.get("doc_id", None)
        title = docs.get("title", "")
        source = docs.get("source", "")
        score = docs.get("score", None)
        snippets = docs.get("all_chunks", [])

        res = {
            "doc_id": doc_id,
            "title": title,
            "source": source,
            "score": score,
            "snippets": snippets,
        }

        RESULT["results"].append(res)

    if mode == "retrieval":
        return RESULT

    if mode == "ai":
        if provider is None:
            print("LLM provider Not Given")
            return RESULT
        prompt = prompt_generation(query, refined_docs)
        llm_response = call_llm.generate(provider=provider, prompt=prompt)

        RESULT["ai_answer"] = llm_response.text
        RESULT["provider"] = llm_response.provider
        RESULT["latency_ms"] = llm_response.latency_ms
        RESULT["llm"] = {
            "prompt_tokens": llm_response.prompt_tokens,
            "completion_tokens": llm_response.completion_tokens,
            "finish_reason": llm_response.finish_reason,
        }

    return RESULT
