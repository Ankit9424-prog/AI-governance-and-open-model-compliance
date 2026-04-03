# scripts/test_retrieval.py

from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient

MODEL_NAME = "BAAI/bge-base-en-v1.5"
QDRANT_PATH = "data/vector_store/qdrant"
COLLECTION_NAME = "ai_governance_chunks"
TOP_K = 5

model = SentenceTransformer(MODEL_NAME)
client = QdrantClient(path=QDRANT_PATH)


def search(query: str, top_k: int = TOP_K):
    query_vector = model.encode(
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

    results = response.points

    print(f"\nQUERY: {query}\n")

    for rank, hit in enumerate(results, start=1):
        payload = hit.payload
        preview = payload["text"][:300].replace("\n", " ")

        print(f"{rank}. score={hit.score:.4f}")
        print(f"   doc_id={payload.get('doc_id')}")
        print(f"   chunk_id={payload.get('chunk_id')}")
        print(f"   section_label={payload.get('section_label')}")
        print(f"   text={preview}")
        print()


def main():
    queries = [
        "What obligations apply to providers of general-purpose AI models?",
        "How does NIST recommend managing generative AI risks?",
        "What secure development guidance is given for AI systems?",
        "What restrictions or permissions are described in model licenses?",
        "What governance requirements are relevant to AI compliance?",
    ]

    for query in queries:
        search(query)


if __name__ == "__main__":
    main()