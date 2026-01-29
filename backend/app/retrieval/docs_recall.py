from app.db.qdrant import search_docs
from app.llm.generation import LLMGeneration, llm_provider, prompt_generation

DEFAULT_LLM = "groq"


def RecallDocs(
    query: str,
    limit: int = 5,
    k: int = 3,
    full_docs: bool = True,
    ai_resp: bool = True,
):
    if full_docs and ai_resp:
        ai_ans = LLMGeneration()
        searched_docs = search_docs(query=query, limit=limit, k=k)
        provider = llm_provider(DEFAULT_LLM)
        prompt = prompt_generation(query)

        relevant_docs = [{doc["title"]: doc["content"]} for doc in searched_docs]
        ai_response = ai_ans.generate(provider, prompt)
        return (relevant_docs, ai_response)

    elif full_docs:
        searched_docs = search_docs(query=query, limit=limit, k=k)

        relevant_docs = [{doc["title"]: doc["content"]} for doc in searched_docs]
        return relevant_docs

    elif ai_resp:
        ai_ans = LLMGeneration()
        provider = llm_provider(DEFAULT_LLM)
        prompt = prompt_generation(query)

        ai_response = ai_ans.generate(provider, prompt)
        return ai_response
