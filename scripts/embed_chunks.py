import json
from pathlib import Path

from sentence_transformers import SentenceTransformer


INPUT_PATH = Path("data/chunks/all_chunks.json")
OUTPUT_PATH = Path("data/chunks/all_chunk_embeddings.json")

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def main():
    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Input file not found: {INPUT_PATH}")

    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    print(f"Loaded {len(chunks)} chunks from {INPUT_PATH}")

    texts = [chunk["text"] for chunk in chunks]

    print(f"Loading embedding model: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)

    print("Generating embeddings...")
    embeddings = model.encode(
        texts,
        show_progress_bar=True,
        normalize_embeddings=True
    )

    results = []
    for chunk, emb in zip(chunks, embeddings):
        results.append({
            "doc_id": chunk["doc_id"],
            "chunk_id": chunk["chunk_id"],
            "section_type": chunk["section_type"],
            "section_label": chunk["section_label"],
            "source_file": chunk["source_file"],
            "text": chunk["text"],
            "embedding": emb.tolist()
        })

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False)

    print(f"Saved embeddings to: {OUTPUT_PATH}")
    print(f"Total embedded chunks: {len(results)}")

    print("\nSample:")
    print("chunk_id:", results[0]["chunk_id"])
    print("embedding length:", len(results[0]["embedding"]))
    print("text preview:", results[0]["text"][:200])


if __name__ == "__main__":
    main()