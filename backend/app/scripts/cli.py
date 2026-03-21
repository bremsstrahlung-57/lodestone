import argparse
import asyncio
import json
import sys

from tqdm import tqdm

from app.db.qdrant import search_docs
from app.ingest.ingestion import ingest_file
from app.llm.generation import LLMGeneration, prompt_generation
from app.retrieval.docs_lodestone import Lodestone
from app.retrieval.retrieve import llm_context_builder


async def ingest_sample_files(args):
    paths = [
        "app/scripts/samples/eldenring.txt",
        "app/scripts/samples/recipe.txt",
        "app/scripts/samples/sample.txt",
        "app/scripts/samples/bloodborne.txt",
        "app/scripts/samples/cp2077.txt",
        "app/scripts/samples/doom.txt",
        "app/scripts/samples/food.txt",
        "app/scripts/samples/gow.txt",
        "app/scripts/samples/history1.txt",
        "app/scripts/samples/history2.txt",
        "app/scripts/samples/hollow_knight.txt",
        "app/scripts/samples/rdr2.txt",
        "app/scripts/samples/recipe.txt",
        "app/scripts/samples/sekiro.txt",
        "app/scripts/samples/space.txt",
        "app/scripts/samples/witcher3.txt",
        "app/scripts/samples/ds3.txt",
    ]

    for path in tqdm(paths, desc="Ingesting files", total=len(paths)):
        await ingest_file(path)


class LodestoneCLI:
    def __init__(
        self, query, limit=5, k=3, mode="retrieval", provider=None, rewrite_query=False
    ):
        self.query = query
        self.limit = limit
        self.k = k
        self.mode = mode
        self.provider = provider
        self.rewrite_query = rewrite_query

    async def search_docs(self):
        results = await search_docs(query=self.query, limit=self.limit, k=self.k)

        if results == []:
            print("Couldn't find any matching data related to your query :(")

        for i in results:
            doc_id = i["doc_id"]
            score = i["score"]
            max_score = i["max_score"]
            source = i["source"]
            title = i["title"]
            doc = i["content"][:100] + "..."
            chunk_doc = i["max_chunk_text"][:100] + "..."
            chunk_id = i["chunk_id"]
            total_chunks = i["total_chunks"]
            created_at = i["created_at"]
            all_scores = i["all_scores"]
            cross_encoder_score = i["cross_encoder_score"]
            normalized_score = i["normalized_score"]
            rank = i["rank"]
            cross_norm = i["cross_norm"]
            cosine_norm = i["cosine_norm"]
            print(
                f"rank: {rank}\n"
                f"title: {title}\n"
                f"doc: {doc}\n"
                f"source: {source}\n"
                f"created_at: {created_at}\n"
                f"doc_id: {doc_id}\n"
                f"normalized_score: {normalized_score}\n"
                f"score: {score}\n"
                f"cross_encoder_score: {cross_encoder_score}\n"
                f"cosine_norm: {cosine_norm}\n"
                f"cross_norm: {cross_norm}\n"
                f"max_score: {max_score}\n"
                f"chunk_doc: {chunk_doc}\n"
                f"chunk_id: {chunk_id}\n"
                f"total_chunks: {total_chunks}\n"
                f"all_scores: {all_scores}\n"
            )

    async def build_llm_context(self):
        result = await search_docs(self.query, self.limit)
        return llm_context_builder(self.query, result)

    async def generate_prompt(self):
        searched_docs = await search_docs(self.query, self.limit, self.k)
        return prompt_generation(self.query, searched_docs)

    async def generate_llm_response(self):
        llm_gen = LLMGeneration()
        prompt = await self.generate_prompt()
        return await llm_gen.generate(self.provider, prompt)

    async def run_lodestone(self):
        rec = await Lodestone.create(
            request_id="cli_lodestone",
            query=self.query,
            limit=self.limit,
            k=self.k,
            mode=self.mode,
            provider=self.provider,
            rewrite_query=self.rewrite_query,
        )
        res = json.dumps(await rec.get_results(), indent=4)
        return res


def _build_cli_instance(args):
    provider = args.provider
    return LodestoneCLI(
        query=args.query,
        limit=args.limit,
        k=args.k,
        mode=args.mode,
        provider=provider,
        rewrite_query=args.rewrite_query,
    )


async def handle_ingest(args):
    await ingest_sample_files(args)


async def handle_search(args):
    cli = _build_cli_instance(args)
    print(f"\nQuery: {args.query}")
    await cli.search_docs()


async def handle_context(args):
    cli = _build_cli_instance(args)
    print(f"\nQuery: {args.query}")
    print(await cli.build_llm_context())


async def handle_prompt(args):
    cli = _build_cli_instance(args)
    print(f"\nQuery: {args.query}")
    print(await cli.generate_prompt())


async def handle_generate(args):
    if not args.provider:
        print("Error: --provider is required for the 'generate' command.")
        sys.exit(1)
    cli = _build_cli_instance(args)
    print(f"\nQuery: {args.query}")
    print(await cli.generate_llm_response())


async def handle_lodestone(args):
    cli = _build_cli_instance(args)
    print(f"\nQuery: {args.query}")
    print(await cli.run_lodestone())


def add_common_args(parser):
    """Add common arguments shared across query-based subcommands."""
    parser.add_argument("query", type=str, help="The search query string")
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Number of documents to retrieve (default: 5)",
    )
    parser.add_argument(
        "--k", type=int, default=3, help="Number of top chunks to consider (default: 3)"
    )
    parser.add_argument(
        "--mode",
        type=str,
        default="retrieval",
        choices=["retrieval", "ai"],
        help="Mode of operation (default: retrieval)",
    )
    parser.add_argument(
        "--provider",
        type=str,
        default=None,
        help="LLM provider name (e.g. gemini, openai)",
    )
    parser.add_argument(
        "--rewrite-query",
        action="store_true",
        default=False,
        help="Enable query rewriting",
    )


async def _run(args):
    try:
        await args.func(args)
    finally:
        from app.db.qdrant import _doc_database

        await _doc_database.close()


def main():
    parser = argparse.ArgumentParser(
        prog="lodestone-cli",
        description="Lodestone CLI — inspect ingestion, search, context building, and LLM generation.",
    )
    subparsers = parser.add_subparsers(
        dest="command", required=True, help="Available commands"
    )

    # --- ingest ---
    ingest_parser = subparsers.add_parser(
        "ingest", help="Ingest all sample files into the database"
    )
    ingest_parser.set_defaults(func=handle_ingest)

    # --- search ---
    search_parser = subparsers.add_parser(
        "search", help="Search documents and display ranked results"
    )
    add_common_args(search_parser)
    search_parser.set_defaults(func=handle_search)

    # --- context ---
    context_parser = subparsers.add_parser(
        "context", help="Build and display the LLM context for a query"
    )
    add_common_args(context_parser)
    context_parser.set_defaults(func=handle_context)

    # --- prompt ---
    prompt_parser = subparsers.add_parser(
        "prompt", help="Generate and display the prompt sent to the LLM"
    )
    add_common_args(prompt_parser)
    prompt_parser.set_defaults(func=handle_prompt)

    # --- generate ---
    generate_parser = subparsers.add_parser(
        "generate", help="Run full LLM generation (requires --provider)"
    )
    add_common_args(generate_parser)
    generate_parser.set_defaults(func=handle_generate)

    # --- lodestone ---
    lodestone_parser = subparsers.add_parser(
        "lodestone", help="Run the full Lodestone pipeline and display results"
    )
    add_common_args(lodestone_parser)
    lodestone_parser.set_defaults(func=handle_lodestone)

    args = parser.parse_args()
    asyncio.run(_run(args))


if __name__ == "__main__":
    main()
