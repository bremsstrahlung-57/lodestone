import json

from tqdm import tqdm

from app.db.qdrant import search_docs
from app.ingest.ingestion import ingest_file
from app.llm.generation import LLMGeneration, llm_provider, prompt_generation
from app.retrieval.docs_recall import Recall
from app.retrieval.retrieve import llm_context_builder


def debug_ingest_file():
    paths = [
        "app/debug/samples/eldenring.txt",
        "app/debug/samples/recipe.txt",
        "app/debug/samples/sample.txt",
        "app/debug/samples/bloodborne.txt",
        "app/debug/samples/cp2077.txt",
        "app/debug/samples/doom.txt",
        "app/debug/samples/food.txt",
        "app/debug/samples/gow.txt",
        "app/debug/samples/history1.txt",
        "app/debug/samples/history2.txt",
        "app/debug/samples/hollow_knight.txt",
        "app/debug/samples/rdr2.txt",
        "app/debug/samples/recipe.txt",
        "app/debug/samples/sekiro.txt",
        "app/debug/samples/space.txt",
        "app/debug/samples/witcher3.txt",
        "app/debug/samples/ds3.txt",
    ]

    for path in tqdm(paths, desc="Ingesting files", total=len(paths)):
        ingest_file(path)


class Debug:
    def __init__(
        self,
        query,
        limit=5,
        k=3,
        mode="retrieval",
        provider=None,
        rewrite_query=False,
    ):
        self.query = query
        self.limit = limit
        self.k = k
        self.mode = mode
        self.provider = provider
        self.rewrite_query = rewrite_query

    def debug_search_docs(self):
        results = search_docs(
            self.query, self.limit, cross_encoder_rerank=self.cross_encoder_rerank
        )
        print(results)
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

            print(
                f"Doc ID: {doc_id}\nScore: {score:.4f}\nCrossEncoder Score: {cross_encoder_score:.4f}\nNormalized Score: {normalized_score}\nMax Score: {max_score:.4f}\nAll Scores: {all_scores}\nSource: {source}\nTitle: {title}\nDoc: {doc}\nChunk Doc: {chunk_doc}\nChunk ID: {chunk_id}\nTotal Chunks: {total_chunks}\nCreated At: {created_at}\n"
            )

    def debug_llm_context_builder(self):
        result = search_docs(self.query, self.limit)
        return llm_context_builder(self.query, result)

    def debug_GenerateLLMContext(self):
        searched_docs = search_docs(self.query, self.limit, self.k)
        generated_context = llm_context_builder(self.query, searched_docs)
        return generated_context

    def debug_prompt_generation(self):
        searched_docs = search_docs(self.query, self.limit, self.k)
        return prompt_generation(self.query, searched_docs)

    def debug_llm_generation(self):
        llm_gen = LLMGeneration()
        prompt = self.debug_prompt_generation()
        return llm_gen.generate(self.provider, prompt)

    def debug_Recall(self):
        debug_rec = Recall(
            query=self.query,
            limit=self.limit,
            k=self.k,
            mode=self.mode,
            provider=self.provider,
            rewrite_query=self.rewrite_query,
        )
        res = json.dumps(debug_rec.get_results(), indent=4)
        return res


def main():
    # debug_ingest_file()
    query = input("Enter Query: ")
    provider = llm_provider("groq")
    debug_instance = Debug(
        query=query,
        limit=20,
        k=10,
        mode="ai",
        provider=provider,
        rewrite_query=True,
    )
    print(f"\nQuery: {query}")
    # print(debug_instance.debug_search_docs())
    # print(debug_instance.debug_llm_context_builder())
    # print(debug_instance.debug_GenerateLLMContext())
    # print(debug_instance.debug_llm_generation())
    print(debug_instance.debug_Recall())


if __name__ == "__main__":
    main()
