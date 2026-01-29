from tqdm import tqdm

from app.db.qdrant import search_docs
from app.ingest.ingestion import ingest_file
from app.llm.generation import LLMGeneration, llm_provider, prompt_generation
from app.retrieval.docs_recall import RecallDocs
from app.retrieval.retrieve import (
    GenerateLLMContext,
    llm_context_builder,
    refine_results,
    retrieve_data,
)


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
    def __init__(self, query, limit=5, k=3):
        self.query = query
        self.limit = limit
        self.k = k

    def debug_search_docs(self):
        print("DEBUG SEARCH DOCS: \n")
        results = search_docs(self.query, self.limit)
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
            stats = i["stats"]

            print(
                f"Doc ID: {doc_id}\nScore: {score:.4f}\nMax Score: {max_score:.4f}\nAll Scores: {all_scores}\nStats: {stats}\nSource: {source}\nTitle: {title}\nDoc: {doc}\nChunk Doc: {chunk_doc}\nChunk ID: {chunk_id}\nTotal Chunks: {total_chunks}\nCreated At: {created_at}\n"
            )

    def debug_retrieve_data(self):
        print("\nDEBUG RETRIEVE DATA: \n")
        res = retrieve_data(self.query, self.limit)
        return res

    def debug_refine_results(self):
        result = search_docs(self.query, self.limit)
        return refine_results(result)

    def debug_llm_context_builder(self):
        result = search_docs(self.query, self.limit)
        ref_result = refine_results(result)
        return llm_context_builder(self.query, ref_result)

    def debug_GenerateLLMContext(self):
        return GenerateLLMContext(self.query)

    def debug_prompt_generation(self):
        return prompt_generation(self.query)

    def debug_llm_generation(self):
        llm_gen = LLMGeneration()
        provider = llm_provider()
        prompt = self.debug_prompt_generation()
        return llm_gen.generate(provider, prompt)

    def debug_RecallDocs(self):
        return RecallDocs(
            query=self.query,
            limit=self.limit,
            k=self.k,
            full_docs=False,
            ai_resp=True,
        )


def main():
    # debug_ingest_file()
    query = input("Enter Query: ")
    limit = int(input("Enter Limit: "))
    k = int(input("Enter top k: "))
    debug_instance = Debug(query, limit, k)
    print(f"\nQuery: {query}")
    # print(debug_instance.debug_search_docs())
    # print(debug_instance.debug_refine_results())
    # print(debug_instance.debug_llm_context_builder())
    # print(debug_instance.debug_GenerateLLMContext())
    # print(debug_instance.debug_llm_generation())
    print(debug_instance.debug_RecallDocs())


if __name__ == "__main__":
    main()
