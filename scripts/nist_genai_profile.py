import re
import json
from pathlib import Path

def clean_nist_table_noise(text: str) -> str:
    # turn table-wrapped subcategory headings into plain lines
    text = re.sub(
        r'(?m)^\|\s*((?:GOVERN|MAP|MEASURE|MANAGE)\s+\d+\.\d+:[^|]+?)\s*\|$',
        r'\1',
        text
    )

    # remove markdown separator rows like |-----...-----|
    text = re.sub(r'(?m)^\|[-:\s|]+\|$', '', text)

    # remove plain long dash lines if they exist
    text = re.sub(r'(?m)^\s*-{5,}\s*$', '', text)

    # collapse extra blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()

def split_nist_actions_chunk(chunk: dict) -> list[dict]:
    text = clean_nist_table_noise(chunk["text"])
    doc_id = chunk["doc_id"]
    source_file = chunk["source_file"]

    # find first RMF subcategory heading like GOVERN 1.1:
    first = re.search(
        r'(?m)^(?:GOVERN|MAP|MEASURE|MANAGE)\s+\d+\.\d+:',
        text
    )

    chunks = []

    # keep the intro before the first subcategory as its own chunk
    if first:
        intro = text[:first.start()].strip()
        rest = text[first.start():]
    else:
        intro = text.strip()
        rest = ""

    if intro:
        chunks.append({
            "doc_id": doc_id,
            "chunk_id": f"{doc_id}_section_15_intro",
            "section_type": "section_intro",
            "section_label": "3. Suggested Actions to Manage GAI Risks",
            "source_file": source_file,
            "text": intro
        })

    pattern = re.compile(
        r'(?ms)^((?:GOVERN|MAP|MEASURE|MANAGE)\s+\d+\.\d+:[^\n]*)\n(.*?)(?=^(?:GOVERN|MAP|MEASURE|MANAGE)\s+\d+\.\d+:[^\n]*|\Z)'
    )

    for i, (subheading, body) in enumerate(pattern.findall(rest), start=1):
        chunks.append({
            "doc_id": doc_id,
            "chunk_id": f"{doc_id}_section_15_sub_{i:02}",
            "section_type": "subsection",
            "section_label": subheading.strip(),
            "source_file": source_file,
            "text": f"{subheading.strip()}\n\n{body.strip()}"
        })

    return chunks

def clean_front_matter(text):
    text = re.sub(r"<!-- image -->", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()

    # remove everything from Table of Contents onward in front matter
    text = re.sub(
        r"(?ms)^##[ \t]+Table of Contents.*$",
        "",
        text
    ).strip()

    return text


def title_block(markdown_text):
    match = re.search(
        r"(?ms)\A(.*?)(?=^##[ \t]+(?:\d+(?:\.\d+)*\.[ \t]+[^\n]+|Appendix[ \t]+[A-Z][^\n]*))",
        markdown_text
    )
    front = match.group(1).strip() if match else markdown_text.strip()
    return clean_front_matter(front)


def normalize_label(heading):
    return re.sub(r"^##[ \t]+", "", heading).strip()


def chunk_nist_sections(
    markdown_text,
    doc_id="nist_genai_ai_profile_001",
    source_file="nist_genai_profile_001.pdf"):

    chunks = []

    front = title_block(markdown_text)
    if front:
        chunks.append({
            "doc_id": doc_id,
            "chunk_id": f"{doc_id}_title_block",
            "section_type": "title_block",
            "section_label": "title_block",
            "source_file": source_file,
            "text": front
        })

    # matches:
    # ## 1. Introduction
    # ## 2.1. Confabulation
    # ## 2.10. Intellectual Property
    # ## Appendix A. Primary GAI Considerations

    sections = re.findall(
        r"(?ms)^(##[ \t]+(?:\d+(?:\.\d+)*\.[ \t]+[^\n]+|Appendix[ \t]+[A-Z][^\n]*))\n(.*?)(?=^##[ \t]+(?:\d+(?:\.\d+)*\.[ \t]+[^\n]+|Appendix[ \t]+[A-Z][^\n]*)|\Z)",
        markdown_text
    )

    for idx, (heading, body) in enumerate(sections, start=1):
        label = normalize_label(heading)
        text = body.strip()

        if not text:
            continue

        # classify section type a bit better
        if label.lower().startswith("appendix"):
            section_type = "appendix"
        elif re.match(r"^\d+\.\d+\.", label):
            section_type = "subsection"
        else:
            section_type = "section"

        chunks.append({
            "doc_id": doc_id,
            "chunk_id": f"{doc_id}_{section_type}_{idx}",
            "section_type": section_type,
            "section_label": label,
            "source_file": source_file,
            "text": text
        })

    fixed_chunks = []

    for chunk in chunks:
        if (
                chunk["doc_id"] == "nist_genai_ai_profile_001"
                and chunk["section_label"] == "3. Suggested Actions to Manage GAI Risks"
        ):
            fixed_chunks.extend(split_nist_actions_chunk(chunk))
        else:
            fixed_chunks.append(chunk)

    return fixed_chunks


if __name__ == "__main__":
    md_path = Path("data/processed/nist_genai_profile_001/parsed.md")
    output_path = Path("data/chunks/nist_genai_profile_001_chunks.json")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    text = md_path.read_text(encoding="utf-8")
    chunks = chunk_nist_sections(text)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(chunks)} chunks to {output_path}")

    # quick debug
    for c in chunks[:5]:
        print("\n---")
        print(c["chunk_id"])
        print(c["section_label"])
        print(c["text"][:300])