# scripts/evaluate_dense_retrieval.py

import json
from pathlib import Path

from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient

MODEL_NAME = "BAAI/bge-base-en-v1.5"
QDRANT_PATH = "data/vector_store/qdrant"
COLLECTION_NAME = "ai_governance_chunks"

EVAL_PATH = Path("data/chunks/retrieval_eval_queries.json")
TOP_K = 5

model = SentenceTransformer(MODEL_NAME)
client = QdrantClient(path=QDRANT_PATH)


def load_eval_queries(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def retrieve(query: str, top_k: int = TOP_K):
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

    return response.points


def evaluate():
    eval_data = load_eval_queries(EVAL_PATH)

    top1_correct = 0
    top3_correct = 0
    top5_correct = 0

    detailed_results = []

    for item in eval_data:
        query = item["query"]
        expected_doc = item["expected_doc"]

        results = retrieve(query, top_k=TOP_K)
        retrieved_docs = [hit.payload.get("doc_id") for hit in results]

        top1_hit = expected_doc in retrieved_docs[:1]
        top3_hit = expected_doc in retrieved_docs[:3]
        top5_hit = expected_doc in retrieved_docs[:5]

        if top1_hit:
            top1_correct += 1
        if top3_hit:
            top3_correct += 1
        if top5_hit:
            top5_correct += 1

        detailed_results.append({
            "query": query,
            "expected_doc": expected_doc,
            "top1_hit": top1_hit,
            "top3_hit": top3_hit,
            "top5_hit": top5_hit,
            "retrieved_docs": retrieved_docs,
            "top_result_chunk_id": results[0].payload.get("chunk_id") if results else None,
            "top_result_section_label": results[0].payload.get("section_label") if results else None,
        })

    total = len(eval_data)

    summary = {
        "total_queries": total,
        "top1_accuracy": top1_correct / total if total else 0,
        "top3_accuracy": top3_correct / total if total else 0,
        "top5_accuracy": top5_correct / total if total else 0,
        "details": detailed_results,
    }

    return summary


def main():
    summary = evaluate()

    print("\n=== DENSE RETRIEVAL EVALUATION ===\n")
    print(f"Total queries: {summary['total_queries']}")
    print(f"Top-1 Accuracy: {summary['top1_accuracy']:.2%}")
    print(f"Top-3 Accuracy: {summary['top3_accuracy']:.2%}")
    print(f"Top-5 Accuracy: {summary['top5_accuracy']:.2%}")

    print("\n=== PER-QUERY RESULTS ===\n")
    for item in summary["details"]:
        print(f"Query: {item['query']}")
        print(f"Expected doc: {item['expected_doc']}")
        print(f"Top-1 hit: {item['top1_hit']}")
        print(f"Top-3 hit: {item['top3_hit']}")
        print(f"Top-5 hit: {item['top5_hit']}")
        print(f"Retrieved docs: {item['retrieved_docs']}")
        print(f"Top result chunk_id: {item['top_result_chunk_id']}")
        print(f"Top result section_label: {item['top_result_section_label']}")
        print("-" * 80)

    report_path = Path("data/manifests/dense_retrieval_eval_report.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    print(f"\nSaved evaluation report to: {report_path}")


if __name__ == "__main__":
    main()