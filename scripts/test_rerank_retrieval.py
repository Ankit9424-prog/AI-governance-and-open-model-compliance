# scripts/test_rerank_retrieval.py

from sentence_transformers import SentenceTransformer, CrossEncoder
from qdrant_client import QdrantClient

EMBED_MODEL_NAME = "BAAI/bge-base-en-v1.5"
RERANK_MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"

QDRANT_PATH = "data/vector_store/qdrant"
COLLECTION_NAME = "ai_governance_chunks"

DENSE_TOP_K = 5
FINAL_TOP_K = 3

embed_model = SentenceTransformer(EMBED_MODEL_NAME)
reranker = CrossEncoder(RERANK_MODEL_NAME)
client = QdrantClient(path=QDRANT_PATH)


def dense_retrieve(query: str, top_k: int = DENSE_TOP_K):
    query_vector = embed_model.encode(
        [query],
        normalize_embeddings=True,
        convert_to_numpy=True
    )[0]

    response = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector.tolist(),
        limit=top_k,
        with_payload=True,
    )

    return response.points


def rerank_results(query: str, results):
    pairs = []
    for hit in results:
        text = hit.payload.get("text", "")
        pairs.append((query, text))

    scores = reranker.predict(pairs)

    reranked = []
    for hit, score in zip(results, scores):
        reranked.append({
            "rerank_score": float(score),
            "dense_score": float(hit.score),
            "payload": hit.payload
        })

    reranked.sort(key=lambda x: x["rerank_score"], reverse=True)
    return reranked


def print_dense(results):
    print("\nDENSE RESULTS:\n")
    for rank, hit in enumerate(results[:FINAL_TOP_K], start=1):
        payload = hit.payload
        preview = payload["text"][:250].replace("\n", " ")
        print(f"{rank}. dense_score={hit.score:.4f}")
        print(f"   doc_id={payload.get('doc_id')}")
        print(f"   chunk_id={payload.get('chunk_id')}")
        print(f"   section_label={payload.get('section_label')}")
        print(f"   text={preview}")
        print()


def print_reranked(results):
    print("\nRERANKED RESULTS:\n")
    for rank, item in enumerate(results[:FINAL_TOP_K], start=1):
        payload = item["payload"]
        preview = payload["text"][:250].replace("\n", " ")
        print(f"{rank}. rerank_score={item['rerank_score']:.4f} | dense_score={item['dense_score']:.4f}")
        print(f"   doc_id={payload.get('doc_id')}")
        print(f"   chunk_id={payload.get('chunk_id')}")
        print(f"   section_label={payload.get('section_label')}")
        print(f"   text={preview}")
        print()


def test_query(query: str):
    print("=" * 100)
    print(f"QUERY: {query}")
    dense_results = dense_retrieve(query, top_k=DENSE_TOP_K)
    print_dense(dense_results)

    reranked_results = rerank_results(query, dense_results)
    print_reranked(reranked_results)


def main():
    queries = [
        "What actions does NIST suggest for managing generative AI risks?",
        "What does NIST say about privacy risks in generative AI?",
        "What obligations apply to providers of general-purpose AI models under the EU AI Act?",
        "What guidance is given for secure AI system development?",
    ]

    for query in queries:
        test_query(query)


if __name__ == "__main__":
    main()