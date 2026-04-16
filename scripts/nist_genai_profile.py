import re
import json
from pathlib import Path


def clean_nist_table_noise(text: str) -> str:
    # turn table-wrapped subcategory headings into plain lines
    text = re.sub(
        r'(?m)^\|\s*((?:GOVERN|MAP|MEASURE|MANAGE)\s+\d+\.\d+:[^|]+?)\s*\|$',
        r'\1',
        text,
    )
    # remove markdown separator rows like |-----...-----|
    text = re.sub(r'(?m)^\|[-:\s|]+\|$', '', text)
    # remove plain long dash lines
    text = re.sub(r'(?m)^\s*-{5,}\s*$', '', text)
    # collapse extra blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def split_rmf_subcategories(chunk: dict, id_prefix: str, section_label: str) -> list[dict]:
    """
    Split a large GOVERN/MAP/MEASURE/MANAGE chunk into per-subcategory chunks.
    Works for both Section 3 and Appendix A bodies.
    """
    text = clean_nist_table_noise(chunk["text"])
    doc_id = chunk["doc_id"]
    source_file = chunk["source_file"]

    # find first RMF subcategory heading like GOVERN 1.1:
    first = re.search(
        r'(?m)^(?:GOVERN|MAP|MEASURE|MANAGE)\s+\d+\.\d+:',
        text,
    )

    chunks = []

    if first:
        intro = text[:first.start()].strip()
        rest = text[first.start():]
    else:
        intro = text.strip()
        rest = ""

    if intro:
        chunks.append({
            "doc_id": doc_id,
            "chunk_id": f"{id_prefix}_intro",
            "section_type": "section_intro",
            "section_label": section_label,
            "source_file": source_file,
            "text": intro,
        })

    pattern = re.compile(
        r'(?ms)^((?:GOVERN|MAP|MEASURE|MANAGE)\s+\d+\.\d+:[^\n]*)\n(.*?)'
        r'(?=^(?:GOVERN|MAP|MEASURE|MANAGE)\s+\d+\.\d+:[^\n]*|\Z)'
    )

    for m in pattern.finditer(rest):
        subheading = m.group(1).strip()
        body = m.group(2).strip()
        # make a stable ID from the subcategory label e.g. GOVERN_1_1
        sub_id = re.sub(r'[^A-Z0-9]', '_', subheading.split(':')[0].upper())
        sub_id = re.sub(r'_+', '_', sub_id).strip('_')
        chunks.append({
            "doc_id": doc_id,
            "chunk_id": f"{id_prefix}_{sub_id}",
            "section_type": "subsection",
            "section_label": subheading,
            "source_file": source_file,
            "text": f"{subheading}\n\n{body}",
        })

    return chunks


def _has_rmf_subcategories(text: str) -> bool:
    return bool(re.search(
        r'(?m)^(?:GOVERN|MAP|MEASURE|MANAGE)\s+\d+\.\d+:',
        text,
    ))


def clean_front_matter(text):
    text = re.sub(r"<!-- image -->", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    text = re.sub(
        r"(?ms)^##[ \t]+Table of Contents.*$",
        "",
        text,
    ).strip()
    return text


def title_block(markdown_text):
    match = re.search(
        r"(?ms)\A(.*?)(?=^##[ \t]+(?:\d+(?:\.\d+)*\.[ \t]+[^\n]+|Appendix[ \t]+[A-Z][^\n]*))",
        markdown_text,
    )
    front = match.group(1).strip() if match else markdown_text.strip()
    return clean_front_matter(front)


def normalize_label(heading):
    return re.sub(r"^##[ \t]+", "", heading).strip()


def chunk_nist_sections(
    markdown_text,
    doc_id="nist_genai_ai_profile_001",
    source_file="nist_genai_profile_001.pdf",
):
    chunks = []

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
        r"(?ms)^(##[ \t]+(?:\d+(?:\.\d+)*\.[ \t]+[^\n]+|Appendix[ \t]+[A-Z][^\n]*))\n(.*?)"
        r"(?=^##[ \t]+(?:\d+(?:\.\d+)*\.[ \t]+[^\n]+|Appendix[ \t]+[A-Z][^\n]*)|\Z)",
        markdown_text,
    )

    raw_chunks = []
    for idx, (heading, body) in enumerate(sections, start=1):
        label = normalize_label(heading)
        text = body.strip()

        if not text:
            continue

        if label.lower().startswith("appendix"):
            section_type = "appendix"
        elif re.match(r"^\d+\.\d+\.", label):
            section_type = "subsection"
        else:
            section_type = "section"

        # stable slug from label: "3. Suggested Actions..." -> "section_3_suggested_actions"
        slug = re.sub(r'[^a-z0-9]+', '_', label.lower()).strip('_')[:60]

        raw_chunks.append({
            "doc_id": doc_id,
            "chunk_id": f"{doc_id}_{section_type}_{slug}",
            "section_type": section_type,
            "section_label": label,
            "source_file": source_file,
            "text": text,
        })

    # Expand any chunk that contains RMF subcategory structure
    for chunk in raw_chunks:
        if _has_rmf_subcategories(chunk["text"]):
            id_prefix = chunk["chunk_id"]
            expanded = split_rmf_subcategories(chunk, id_prefix, chunk["section_label"])
            chunks.extend(expanded)
        else:
            chunks.append(chunk)

    return chunks


if __name__ == "__main__":
    md_path = Path("data/processed/nist_genai_profile_001/parsed.md")
    output_path = Path("data/chunks/nist_genai_profile_001_chunks.json")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    text = md_path.read_text(encoding="utf-8")
    chunks = chunk_nist_sections(text)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(chunks)} chunks to {output_path}")

    for c in chunks[:5]:
        print("\n---")
        print(c["chunk_id"])
        print(c["section_label"])
        print(c["text"][:300])
