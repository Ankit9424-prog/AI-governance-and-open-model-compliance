"""
retrieval.py — Hybrid BM25 + dense retrieval with Reciprocal Rank Fusion (RRF)

Two search methods are combined:
  - Dense  : finds chunks that are *semantically similar* to the question
  - BM25   : finds chunks that contain the same *keywords* as the question
  - RRF    : merges the two ranked lists into a single ranked list

This helps when dense search misses an exact keyword match (and vice versa).
"""

import json
from pathlib import Path

from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient

CHUNKS_PATH = Path("data/chunks/all_chunks_clean.json")
QDRANT_PATH = "data/vector_store/qdrant"
COLLECTION_NAME = "ai_governance_chunks"

# RRF constant — standard value, no need to change
RRF_K = 60


def load_chunks(path: Path = CHUNKS_PATH) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def tokenize(text: str) -> list[str]:
    """Split text into lowercase words for BM25."""
    return text.lower().split()


def bm25_search(question: str, chunks: list[dict], top_k: int) -> list[dict]:
    """
    Keyword search: score each chunk by how many question words it contains.
    Returns top_k chunks with a bm25_score field added.
    """
    corpus = [tokenize(c["text"]) for c in chunks]
    bm25 = BM25Okapi(corpus)
    scores = bm25.get_scores(tokenize(question))

    ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[:top_k]

    return [
        {**chunks[idx], "bm25_score": float(score)}
        for idx, score in ranked
        if score > 0
    ]


def dense_search(
    question: str,
    embed_model: SentenceTransformer,
    qdrant_client: QdrantClient,
    top_k: int,
) -> list[dict]:
    """
    Semantic search: find chunks whose meaning is closest to the question.
    Returns top_k chunks with a score field added.
    """
    vector = embed_model.encode(
        [question], normalize_embeddings=True, convert_to_numpy=True
    )[0]

    hits = qdrant_client.query_points(
        collection_name=COLLECTION_NAME,
        query=vector.tolist(),
        limit=top_k,
    ).points

    return [
        {
            "score": float(hit.score),
            "doc_id": hit.payload.get("doc_id"),
            "chunk_id": hit.payload.get("chunk_id"),
            "section_type": hit.payload.get("section_type"),
            "section_label": hit.payload.get("section_label"),
            "text": hit.payload.get("text", ""),
            "source_file": hit.payload.get("source_file"),
        }
        for hit in hits
    ]


def rrf_fuse(
    dense_results: list[dict],
    bm25_results: list[dict],
    top_k: int,
) -> list[dict]:
    """
    Reciprocal Rank Fusion: merge two ranked lists into one.

    For every chunk, add up 1/(RRF_K + rank) from each list it appears in.
    A chunk near the top of both lists gets the highest combined score.
    """
    scores: dict[str, float] = {}
    chunks_by_id: dict[str, dict] = {}

    for rank, chunk in enumerate(dense_results, start=1):
        cid = chunk["chunk_id"]
        scores[cid] = scores.get(cid, 0) + 1 / (RRF_K + rank)
        chunks_by_id[cid] = chunk

    for rank, chunk in enumerate(bm25_results, start=1):
        cid = chunk["chunk_id"]
        scores[cid] = scores.get(cid, 0) + 1 / (RRF_K + rank)
        chunks_by_id[cid] = chunk

    top_ids = sorted(scores, key=lambda cid: scores[cid], reverse=True)[:top_k]

    return [
        {**chunks_by_id[cid], "rrf_score": round(scores[cid], 6)}
        for cid in top_ids
    ]


def hybrid_search(
    question: str,
    embed_model: SentenceTransformer,
    qdrant_client: QdrantClient,
    all_chunks: list[dict],
    top_k: int = 8,
) -> list[dict]:
    """
    Main entry point. Run both searches and return a fused ranked list.
    """
    dense = dense_search(question, embed_model, qdrant_client, top_k)
    bm25 = bm25_search(question, all_chunks, top_k)
    return rrf_fuse(dense, bm25, top_k)
