import re
import json
from pathlib import Path

MIN_CHUNK_CHARS = 300  # skip near-empty chunks (outline bullets, stubs)


def clean_front_matter(text):
    text = re.sub(r"<!-- image -->", "", text)
    text = re.sub(
        r"(?ms)^##[ \t]+Contents\s*\n.*?(?=^##[ \t]+[^\n]+|\Z)",
        "",
        text,
    )
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text


def clean_body_text(text):
    text = re.sub(r"<!-- image -->", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text


def title_block(markdown_text):
    match = re.search(
        r"(?ms)\A(.*?)(?=^##[ \t]+\d+\.[ \t]+[^\n]+)",
        markdown_text,
    )
    front = match.group(1).strip() if match else markdown_text.strip()
    return clean_front_matter(front)


def normalize_label(heading):
    return re.sub(r"^##[ \t]+", "", heading).strip()


def chunk_ncsc_sections(
    markdown_text,
    doc_id="ncsc_secure_ai_001",
    source_file="ncsc_secure_ai_001.pdf",
):
    chunks = []

    skip_labels = {
        "Guidelines for secure AI system development",
        "About this document",
        "Acknowledgements",
        "Disclaimer",
        "Contents",
        "Executive summary",
        "About the guidelines",
        # "Further reading" is the section header — we skip the entire section
        # by catching it below (all headings inside it are bibliography refs)
    }

    # The four numbered phase labels appear twice in the document:
    # first as a short outline summary, then again with full content.
    # We track which ones we've already emitted and only keep the first
    # occurrence that meets the minimum length threshold.
    seen_labels: dict[str, int] = {}  # label -> best chunk char count so far

    front = title_block(markdown_text)
    if front:
        chunks.append({
            "doc_id": doc_id,
            "chunk_id": f"{doc_id}_title_block",
            "section_type": "title_block",
            "section_label": "title_block",
            "source_file": source_file,
            "text": front,
        })

    sections = re.findall(
        r"(?ms)^(##[ \t]+[^\n]+)\n(.*?)(?=^##[ \t]+[^\n]+|\Z)",
        markdown_text,
    )

    # Two-pass approach:
    # Pass 1 — collect all candidate (label, text, idx) tuples
    # Pass 2 — for duplicate labels keep the longer one
    candidates = []
    in_further_reading = False

    for idx, (heading, body) in enumerate(sections, start=1):
        label = normalize_label(heading)

        if label in skip_labels:
            in_further_reading = False
            continue

        # "Further reading" section: skip this heading and everything after
        # it that looks like a bibliography reference (short, no real content)
        if label == "Further reading":
            in_further_reading = True
            continue

        if in_further_reading:
            # Once we hit "Notes" or similar non-bibliography heading, stop skipping
            if re.match(r'^Notes?$', label, re.IGNORECASE):
                in_further_reading = False
            else:
                continue

        text = clean_body_text(body)
        if not text:
            continue

        candidates.append((label, text, idx))

    # Resolve duplicates: for each label keep the candidate with the most chars
    best: dict[str, tuple] = {}  # label -> (label, text, idx)
    for label, text, idx in candidates:
        if label not in best or len(text) > len(best[label][1]):
            best[label] = (label, text, idx)

    # Emit in original document order (by idx)
    ordered = sorted(best.values(), key=lambda x: x[2])

    for label, text, idx in ordered:
        if len(text) < MIN_CHUNK_CHARS:
            continue

        chunks.append({
            "doc_id": doc_id,
            "chunk_id": f"{doc_id}_section_{idx}",
            "section_type": "section",
            "section_label": label,
            "source_file": source_file,
            "text": text,
        })

    return chunks


if __name__ == "__main__":
    md_path = Path("data/processed/ncsc_secure_ai_001/parsed.md")
    output_path = Path("data/chunks/ncsc_secure_ai_001_chunks.json")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    text = md_path.read_text(encoding="utf-8")
    chunks = chunk_ncsc_sections(text)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(chunks)} chunks to {output_path}")
