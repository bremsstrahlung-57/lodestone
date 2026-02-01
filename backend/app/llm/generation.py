import time

from app.llm.client import LLMResponse
from app.llm.factory import LLMFactory
from app.retrieval.retrieve import llm_context_builder


class LLMGeneration:
    def generate(
        self,
        provider: str,
        prompt: str,
        api_key: str | None = None,
        model: str | None = None,
    ) -> LLMResponse:
        llm = LLMFactory.create(
            provider=provider,
            api_key=api_key,
            model=model,
        )

        start = time.perf_counter()
        raw = llm.generate(prompt)
        latency_ms = (time.perf_counter() - start) * 1000

        return llm.parse_response(raw, latency_ms)


def prompt_generation(query, refined_result):
    context = llm_context_builder(query, refined_result)
    prompt = [
        "Query:",
        query,
        "Context:",
        "The following is a list of text chunks retrieved from documents.",
        "Each chunk is independent and may overlap.",
    ]
    for res in context["context"]:
        title = res["title"]
        score = res["score"]
        source = res["source"]
        chunks = res["chunks"]
        chunk = f"Title: {title} | Score: {score} | Source: {source}\nText/Docs/Chunks: {chunks}\n"
        prompt.append(chunk)

    prompt.append("""Task:
Using only the information in the context above, answer the query.
Do not add information that is not present.
Do not explain why an answer is correct. Only state the answer itself.""")

    return "\n".join(prompt)


def llm_provider(default=None):
    llm_providers = ["gemini", "groq"]

    if default is not None:
        return default
    elif default not in llm_providers:
        pass

    print("API Available\n1.Gemini\n2.LLama(Groq)")
    num = int(input("Choose provider: "))
    match num:
        case 1:
            return "gemini"
        case 2:
            return "groq"
        case _:
            return "groq"
