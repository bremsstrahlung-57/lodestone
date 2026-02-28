import logging

from app.db.qdrant import fetch_chunk_by_ids

logger = logging.getLogger(__name__)


def expand_chunk_ids(chunk_ids, total_chunks):
    window = set()
    for cid in chunk_ids:
        for x in (cid - 1, cid, cid + 1):
            if 0 <= x < total_chunks:
                window.add(x)

    expanded = sorted(window)
    logger.debug(
        "expanded chunk window",
        extra={
            "input_ids": chunk_ids,
            "expanded_ids": expanded,
            "total_chunks": total_chunks,
        },
    )
    return expanded


def get_evidence_chunks(all_chunks):
    return sorted(
        all_chunks,
        key=lambda c: c["score"],
        reverse=True,
    )


async def build_context(doc_id, evidence, total_chunks):
    hit_ids = [e["chunk_id"] for e in evidence]
    window_ids = expand_chunk_ids(hit_ids, total_chunks)
    window_ids = list(set(window_ids))

    points = await fetch_chunk_by_ids(doc_id, window_ids)
    points.sort(key=lambda p: p.payload["chunk_id"])
    context_list = set()
    for p in points:
        context_list.add(p.payload["text"])

    logger.debug(
        "built context for document",
        extra={
            "doc_id": doc_id,
            "hit_chunks": len(hit_ids),
            "window_chunks": len(window_ids),
            "context_pieces": len(context_list),
        },
    )
    return list(context_list)


def llm_context_builder(query, result):
    ref_res = result
    llm_context = {"query": query, "context": []}
    for res in ref_res:
        title = res["title"]
        score = res["score"]
        source = res["source"]
        chunks = res["all_chunks"]
        llm_context["context"].append(
            {
                "title": title,
                "score": score,
                "source": source,
                "chunks": chunks,
            }
        )

    logger.debug(
        "built LLM context",
        extra={"query": query, "context_docs": len(llm_context["context"])},
    )
    return llm_context
