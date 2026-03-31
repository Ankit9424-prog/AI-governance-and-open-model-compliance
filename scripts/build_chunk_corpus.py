import json
from pathlib import Path

CHUNK_FILES = [
    "data/chunks/eu_ai_act_001_chunks.json",
    "data/chunks/nist_genai_profile_001_chunks.json",
    "data/chunks/ncsc_secure_ai_001_chunks.json",
]

OUTPUT_PATH = Path("data/chunks/all_chunks.json")

REQUIRED_KEYS = {
    "doc_id",
    "chunk_id",
    "section_type",
    "section_label",
    "source_file",
    "text",
}

def load_chunks(file_path):
    path = Path(file_path)

    if not path.exists():
        print(f"[WARNING] File not found: {path}")
        return []

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        print(f"[WARNING] Expected a list in {path}, got {type(data).__name__}")
        return []

    return data


def validate_chunk(chunk, file_path, index):
    missing = REQUIRED_KEYS - set(chunk.keys())
    if missing:
        print(f"[WARNING] Missing keys in {file_path} chunk #{index}: {missing}")
        return False

    if not isinstance(chunk["text"], str) or not chunk["text"].strip():
        print(f"[WARNING] Empty text in {file_path} chunk #{index}")
        return False

    return True


def deduplicate_chunks(chunks):
    seen = set()
    unique_chunks = []

    for chunk in chunks:
        key = (
            chunk["doc_id"],
            chunk["chunk_id"],
            chunk["text"].strip(),
        )

        if key in seen:
            continue

        seen.add(key)
        unique_chunks.append(chunk)

    return unique_chunks


def main():
    all_chunks = []

    for file_path in CHUNK_FILES:
        chunks = load_chunks(file_path)
        print(f"Loaded {len(chunks)} chunks from {file_path}")

        valid_chunks = []
        for i, chunk in enumerate(chunks, start=1):
            if validate_chunk(chunk, file_path, i):
                valid_chunks.append(chunk)

        print(f"Kept {len(valid_chunks)} valid chunks from {file_path}")
        all_chunks.extend(valid_chunks)

    print(f"\nTotal before deduplication: {len(all_chunks)}")
    all_chunks = deduplicate_chunks(all_chunks)
    print(f"Total after deduplication: {len(all_chunks)}")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)

    print(f"\nSaved merged chunk corpus to: {OUTPUT_PATH}")

    # quick preview
    print("\nSample chunks:")
    for chunk in all_chunks[:5]:
        print("-" * 60)
        print("chunk_id:", chunk["chunk_id"])
        print("section_label:", chunk["section_label"])
        print("text preview:", chunk["text"][:200])


if __name__ == "__main__":
    main()