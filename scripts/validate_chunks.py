import json
import re
from pathlib import Path

INPUT_PATH = Path("data/chunks/all_chunks.json")
OUTPUT_PATH = Path("data/chunks/all_chunks_clean.json")
REPORT_PATH = Path("data/manifests/chunk_validation_report.json")

REQUIRED_FIELDS = [
    "doc_id",
    "chunk_id",
    "section_type",
    "section_label",
    "source_file",
    "text",
]

MIN_TEXT_CHARS = 40
MAX_TEXT_WORDS_SOFT = 3000


SEPARATOR_LINE_RE = re.compile(r"^\s*[\|\-\:_]{5,}\s*$")
MULTI_PUNCT_RE = re.compile(r"[-=_]{8,}")
WHITESPACE_RE = re.compile(r"\s+")

def normalize_text(text: str) -> str:
    lines = []

    for line in text.splitlines():
        if SEPARATOR_LINE_RE.match(line):
            continue
        lines.append(line)

    text = "\n".join(lines)
    text = MULTI_PUNCT_RE.sub(" ", text)
    text = WHITESPACE_RE.sub(" ", text).strip()

    return text

def estimate_token_count(text: str) -> int:
    # rough estimate; fine for maetadata/sanity check
    return max(1, len(text) // 4)

def main():
    data = json.loads(INPUT_PATH.read_text(encoding="utf-8"))

    clean_chunks = []
    report = {
        "input_count": len(data),
        "kept_count": 0,
        "dropped_missing_fields": [],
        "dropped_empty_text": [],
        "dropped_too_short": [],
        "dropped_duplicate_chunk_id": [],
        "dropped_duplicate_text": [],
        "flagged_too_long": [],
        "flagged_suspicious": [],
    }

    seen_chunk_ids = set()
    seen_texts = set()

    for chunk in data:
        missing = [f for f in REQUIRED_FIELDS if f not in chunk]
        if missing:
            report["dropped_missing_fields"].append({
                "chunk": chunk,
                "missing_fields": missing
            })
            continue

        raw_text = str(chunk["text"])
        clean_text = normalize_text(raw_text)

        if not clean_text:
            report["dropped_empty_text"].append(chunk["chunk_id"])
            continue


        if len(clean_text) < MIN_TEXT_CHARS and chunk["doc_id"] != "eu_ai_act_001":
            report["dropped_too_short"].append(chunk["chunk_id"])
            continue

        chunk_key = (chunk["doc_id"], chunk["chunk_id"])
        if chunk_key in seen_chunk_ids:
            report["dropped_duplicate_chunk_id"].append(chunk["chunk_id"])
            continue
        seen_chunk_ids.add(chunk_key)

        text_key = clean_text.lower()
        if text_key in seen_texts:
            report["dropped_duplicate_text"].append(chunk["chunk_id"])
            continue
        seen_texts.add(text_key)

        word_count = len(clean_text.split())
        if word_count > MAX_TEXT_WORDS_SOFT:
            report["flagged_too_long"].append({
                "chunk_id": chunk["chunk_id"],
                "word_count": word_count
            })

        suspicious_score = 0
        if clean_text.count("|") > 20:
            suspicious_score += 1
        if clean_text.count("-----") > 0:
            suspicious_score += 1
        if len(set(clean_text)) < 15:
            suspicious_score += 1

        if suspicious_score >= 2:
            report["flagged_suspicious"].append(chunk["chunk_id"])

        chunk["text"] = clean_text
        chunk["char_len"] = len(clean_text)
        chunk["token_estimate"] = estimate_token_count(clean_text)

        clean_chunks.append(chunk)

    report["kept_count"] = len(clean_chunks)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    OUTPUT_PATH.write_text(
        json.dumps(clean_chunks, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    REPORT_PATH.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    print(f"Input chunks: {report['input_count']}")
    print(f"Kept chunks: {report['kept_count']}")
    print(f"Saved cleaned chunks to: {OUTPUT_PATH}")
    print(f"Saved report to: {REPORT_PATH}")


if __name__ == "__main__":
    main()
