# scripts/test_retrieval.py
import json
from pathlib import Path

from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient

MODEL_NAME = "BAAI/bge-base-en-v1.5"
QDRANT_PATH = "data/vector_store/qdrant"
COLLECTION_NAME = "ai_governance_chunks"
TOP_K = 8

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

    query_results = []

    for rank, hit in enumerate(results, start=1):
        payload = hit.payload
        preview = payload["text"][:300].replace("\n", " ")

        print(f"{rank}. score={hit.score:.4f}")
        print(f"   doc_id={payload.get('doc_id')}")
        print(f"   chunk_id={payload.get('chunk_id')}")
        print(f"   section_label={payload.get('section_label')}")
        print(f"   text={preview}")
        print()

        query_results.append({
            "rank": rank,
            "score": hit.score,
            "doc_id": payload.get("doc_id"),
            "chunk_id": payload.get("chunk_id"),
            "section_label": payload.get("section_label"),
            "text_preview": preview,
        })

    return {
        "query": query,
        "results": query_results
    }


def main():
    queries = [
        "What obligations apply to providers of general-purpose AI models under the EU AI Act?",
        "How does the EU AI Act describe general-purpose AI models?",
        "What risks of generative AI are described in the NIST GenAI Profile?",
        "What actions does NIST suggest for managing generative AI risks?",
        "What does NIST say about privacy risks in generative AI?",
        "What guidance is given for secure AI system development?",
        "What does the secure AI guidance say about secure deployment and maintenance?",
        "What governance and compliance requirements are mentioned across these AI documents?",
    ]

    all_results = []

    for query in queries:
        result = search(query)
        all_results.append(result)

    report_path = Path("data/manifests/retrieval_smoke_test.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(all_results, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    client.close()

    print("Done.")
    print(f"Saved retrieval report to: {report_path}")


if __name__ == "__main__":
    main()