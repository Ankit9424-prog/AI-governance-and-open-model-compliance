# scripts/embed_chunks_qdrant.py

import json
from pathlib import Path
from typing import List

from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

CHUNKS_PATH = Path("data/chunks/all_chunks_clean.json")
QDRANT_PATH = "data/vector_store/qdrant"
COLLECTION_NAME = "ai_governance_chunks"

MODEL_NAME = "BAAI/bge-base-en-v1.5"
BATCH_SIZE = 32


def load_chunks(path: Path) -> List[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_payload(chunk: dict) -> dict:
    return {
        "doc_id": chunk["doc_id"],
        "chunk_id": chunk["chunk_id"],
        "section_type": chunk["section_type"],
        "section_label": chunk["section_label"],
        "source_file": chunk["source_file"],
        "text": chunk["text"],
        "char_len": chunk.get("char_len"),
        "token_estimate": chunk.get("token_estimate"),
        "doc_type": chunk.get("doc_type"),
        "jurisdiction": chunk.get("jurisdiction"),
        "issuer": chunk.get("issuer"),
        "language": chunk.get("language", "en"),
    }


def main():
    chunks = load_chunks(CHUNKS_PATH)
    texts = [chunk["text"] for chunk in chunks]

    print(f"Loaded {len(chunks)} chunks")

    model = SentenceTransformer(MODEL_NAME)

    embeddings = model.encode(
        texts,
        batch_size=BATCH_SIZE,
        show_progress_bar=True,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )

    vector_size = embeddings.shape[1]
    print(f"Embedding shape: {embeddings.shape}")

    client = QdrantClient(path=QDRANT_PATH)

    if client.collection_exists(COLLECTION_NAME):
        client.delete_collection(COLLECTION_NAME)

    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=vector_size,
            distance=Distance.COSINE,
        ),
    )

    points = []
    for idx, (chunk, vector) in enumerate(zip(chunks, embeddings)):
        payload = build_payload(chunk)
        points.append(
            PointStruct(
                id=idx,
                vector=vector.tolist(),
                payload=payload,
            )
        )

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points,
    )

    report = {
        "collection_name": COLLECTION_NAME,
        "vector_db_path": QDRANT_PATH,
        "embedding_model": MODEL_NAME,
        "num_chunks_indexed": len(chunks),
        "vector_size": vector_size,
    }

    report_path = Path("data/manifests/embedding_index_report.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("Done.")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()