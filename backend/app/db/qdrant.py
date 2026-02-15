import logging
import uuid
from math import exp
from statistics import mean

from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.exceptions import UnexpectedResponse
from qdrant_client.models import Distance, PointStruct, VectorParams
from sentence_transformers import CrossEncoder

from app.core.constants import COLLECTION_NAME, EMBEDDING_DIM
from app.core.settings import settings
from app.db.sqlitedb import SQLiteDB
from app.embeddings.minilm import embed

logger = logging.getLogger(__name__)

_client: QdrantClient | None = None
_collection_checked = False
doc_database = SQLiteDB()
cross_encoder = CrossEncoder("cross-encoder/ms-marco-TinyBERT-L2-v2")


def get_qdrant_client() -> QdrantClient:
    """Creates QDrant Client if doesn't exist and returns it"""
    global _client, _collection_checked

    if _client is None:
        logger.info("creating Qdrant client", extra={"url": settings.qdrant_url})
        _client = QdrantClient(url=settings.qdrant_url)
        logger.info("Qdrant client created")

    if not _collection_checked:
        ensure_collection_exists(
            client=_client,
            collection_name=COLLECTION_NAME,
            vector_size=EMBEDDING_DIM,
        )
        _collection_checked = True

    return _client


def ping_qdrant() -> None:
    logger.info("pinging Qdrant")
    try:
        get_qdrant_client()
        logger.info("Qdrant ping successful")
    except Exception:
        logger.exception("Qdrant ping failed")
        raise


def _assert_embedding_dim():
    """Check for right dimensions"""
    logger.info("asserting embedding dimensions", extra={"expected": EMBEDDING_DIM})
    vec = embed("dim check")
    if len(vec) != EMBEDDING_DIM:
        logger.error(
            "embedding dim mismatch",
            extra={"expected": EMBEDDING_DIM, "got": len(vec)},
        )
        raise RuntimeError(
            f"Embedding dim mismatch: expected {EMBEDDING_DIM}, got {len(vec)}"
        )
    logger.info("embedding dim check passed", extra={"dim": len(vec)})


def ensure_collection_exists(
    client: QdrantClient, collection_name: str, vector_size: int
) -> None:
    try:
        client.get_collection(collection_name)
        logger.debug("collection already exists", extra={"collection": collection_name})
        return
    except UnexpectedResponse as e:
        if e.status_code != 404:
            logger.exception(
                "unexpected error checking collection",
                extra={"collection": collection_name},
            )
            raise

    logger.info(
        "creating collection",
        extra={"collection": collection_name, "vector_size": vector_size},
    )
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(
            size=vector_size,
            distance=Distance.COSINE,
        ),
    )
    logger.info("collection created", extra={"collection": collection_name})


def filter_results(
    results: list[dict],
    *,
    min_normalized: float = 0.35,
    drop_ratio: float = 0.25,
    fallback_top_k: int = 3,
):
    if not results:
        return []

    best = results[0]["normalized_score"]

    filtered = []
    prev_score = best

    for i, r in enumerate(results):
        ns = r["normalized_score"]

        if ns < min_normalized:
            break
        if ns < best * drop_ratio:
            break
        if i > 0 and prev_score > 0 and (prev_score - ns) / prev_score > 0.4:
            break

        filtered.append(r)
        prev_score = ns

    if len(filtered) < fallback_top_k:
        return results[:fallback_top_k]

    return filtered


def normalize_score(results, a=0.4, e=1e-8):
    """Normalize and combine cosine + cross-encoder scores"""
    if not results:
        return

    for item in results:
        cosine_score = item["score"]
        cross_encoder_score = item["cross_encoder_score"]

        cross_norm = 1 / (1 + exp(-cross_encoder_score))

        final_score = a * cosine_score + (1 - a) * cross_norm

        item["normalized_score"] = final_score
        item["cross_norm"] = cross_norm


def search_docs(query, limit=5, k=3):
    """Search for a query from the Vector DB"""
    logger.info("searching docs", extra={"query": query, "limit": limit, "k": k})

    client: QdrantClient = get_qdrant_client()
    query_vector = embed(text=query)

    search_results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=limit,
        with_vectors=False,
    )

    logger.debug(
        "raw search results received",
        extra={"points_returned": len(search_results.points)},
    )

    doc_score_map = {}

    for item in search_results.points:
        doc_id = item.payload.get("doc_id")
        score = item.score
        text = item.payload.get("text", "")
        chunk_id = item.payload.get("chunk_id")

        if doc_id not in doc_score_map:
            doc_score_map[doc_id] = {
                "max_score": score,
                "text": text,
                "chunk_id": chunk_id,
                "all_scores": [score],
                "chunks": [
                    {
                        "chunk_id": chunk_id,
                        "text": text,
                        "score": score,
                    }
                ],
            }
        else:
            doc_score_map[doc_id]["max_score"] = max(
                doc_score_map[doc_id]["max_score"], score
            )
            doc_score_map[doc_id]["all_scores"].append(score)
            if not any(
                c["chunk_id"] == chunk_id for c in doc_score_map[doc_id]["chunks"]
            ):
                doc_score_map[doc_id]["chunks"].append(
                    {
                        "chunk_id": chunk_id,
                        "text": text,
                        "score": score,
                    }
                )

    logger.debug(
        "doc score map built",
        extra={"unique_docs": len(doc_score_map)},
    )

    doc_db = doc_database.read_from_cache()
    results = []

    for row in doc_db:
        doc_id = row[0]
        if doc_id in doc_score_map:
            chunks = doc_score_map[doc_id]["chunks"]

            sorted_chunks = sorted(
                chunks,
                key=lambda c: c["score"],
                reverse=True,
            )
            topk_chunks = [
                {
                    "chunk_id": c["chunk_id"],
                    "score": c["score"],
                    "text": c["text"],
                }
                for c in sorted_chunks[:k]
            ]

            best_chunk = topk_chunks[0]
            scores = [c["score"] for c in chunks]
            topk_score = mean(scores[:k])

            results.append(
                {
                    "doc_id": doc_id,
                    "score": topk_score,
                    "max_score": best_chunk["score"],
                    "title": row[1],
                    "content": row[2],
                    "max_chunk_text": best_chunk["text"],
                    "source": row[3],
                    "total_chunks": row[4],
                    "chunk_id": best_chunk["chunk_id"],
                    "all_chunks": topk_chunks,
                    "created_at": row[5],
                    "all_scores": scores,
                }
            )

    results.sort(key=lambda item: item["score"], reverse=True)

    pairs = []
    for item in results:
        title = item["title"]
        text = item["content"]
        pairs.append([query, f"{title}-{text}"])
    cross_encoder_scores = cross_encoder.predict(pairs)

    for i, item in enumerate(results):
        item["cross_encoder_score"] = cross_encoder_scores[i]

    normalize_score(results)
    results.sort(key=lambda item: item["normalized_score"], reverse=True)

    final_res = filter_results(
        results,
        min_normalized=0.35,
        drop_ratio=0.25,
        fallback_top_k=k,
    )

    logger.info(
        "search complete",
        extra={
            "query": query,
            "total_matched": len(results),
            "after_filtering": len(final_res),
        },
    )

    return final_res


def ingest_data(docs):
    """Upsert data in Vector DB"""
    logger.info("ingesting data into Qdrant", extra={"doc_count": len(docs)})

    client: QdrantClient = get_qdrant_client()
    points = []
    for doc in docs:
        text = doc["text"]
        doc_id = doc["doc_id"]
        chunk_id = doc["chunk_id"]
        point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{doc_id}_{chunk_id}"))

        points.append(
            PointStruct(
                id=point_id,
                vector=embed(text),
                payload={
                    "text": text,
                    "source": "debug",
                    "doc_id": doc_id,
                    "chunk_id": chunk_id,
                },
            )
        )

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points,
    )

    logger.info(
        "data ingested successfully",
        extra={"points_upserted": len(points), "collection": COLLECTION_NAME},
    )

    return client.get_collection(COLLECTION_NAME)


def fetch_chunk_by_ids(doc_id, chunk_ids):
    logger.debug(
        "fetching chunks by ids",
        extra={"doc_id": doc_id, "chunk_ids": chunk_ids},
    )

    client = get_qdrant_client()

    result = client.scroll(
        collection_name=COLLECTION_NAME,
        scroll_filter=models.Filter(
            must=[
                models.FieldCondition(
                    key="doc_id",
                    match=models.MatchValue(value=doc_id),
                ),
                models.FieldCondition(
                    key="chunk_id",
                    match=models.MatchAny(any=chunk_ids),
                ),
            ]
        ),
        with_vectors=False,
        limit=len(chunk_ids),
    )
    points, _ = result

    logger.debug(
        "chunks fetched",
        extra={"doc_id": doc_id, "requested": len(chunk_ids), "returned": len(points)},
    )

    return points
