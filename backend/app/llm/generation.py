import logging

from app.llm.client import LLMResponse
from app.llm.factory import LLMFactory
from app.retrieval.retrieve import llm_context_builder

logger = logging.getLogger(__name__)


class LLMGeneration:
    async def generate(self, provider: str, prompt: str) -> LLMResponse:
        logger.info(
            "starting LLM generation",
            extra={"provider": provider, "prompt_length": len(prompt)},
        )

        llm = LLMFactory.create(
            provider=provider,
        )

        response = await llm.generate(prompt)
        return response

    async def rewrite_query(self, query: str, provider: str) -> str:
        logger.info(
            "starting query rewriting",
            extra={"user_query": query, "provider": provider},
        )

        llm = LLMFactory.create(
            provider=provider,
        )

        rewritten_query = await llm.query_rewrite(query)
        return rewritten_query if rewritten_query is not None else query


def prompt_generation(query, result):
    context = llm_context_builder(query, result)

    prompt_parts = []

    prompt_parts.append("""<instructions>
You are answering a user's question based on their personal documents. Talk like a person — clear, direct, no unnecessary formality.

Answer only from what's in the <context> below. If the context doesn't have enough to answer, say so plainly — something like "I don't see anything in your documents about that." If documents contradict each other, call it out naturally. Don't invent information that isn't there.
</instructions>""")

    prompt_parts.append("<context>")
    prompt_parts.append(
        "The following are text chunks retrieved from the user's documents. Each chunk is independent and may overlap."
    )
    for res in context["context"]:
        title = res["title"]
        source = res["source"]
        chunks = res["chunks"]
        prompt_parts.append(
            f'<document title="{title}" source="{source}">\n{chunks}\n</document>'
        )
    prompt_parts.append("</context>")

    prompt_parts.append(f"<user_query>\n{query}\n</user_query>")

    prompt_parts.append("""<reminder>
Answer the question in <user_query> using only what's in <context>.
</reminder>""")

    built = "\n\n".join(prompt_parts)
    logger.debug(
        "prompt generated",
        extra={
            "query": query,
            "context_docs": len(context["context"]),
            "prompt_length": len(built),
        },
    )
    return built
