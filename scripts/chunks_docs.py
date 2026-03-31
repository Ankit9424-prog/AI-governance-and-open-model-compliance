import re
import json
from pathlib import Path


def title_block(markdown_text):
    match = re.search(r"(?s)\A(.*?)(?=\n##\s*Whereas:)", markdown_text, flags=re.DOTALL | re.MULTILINE)
    return match.group(1).strip() if match else ""

def split_recitals(markdown_text, group_size=4):
    match = re.search(
        r'(## Whereas:\s*)(.*?)(?=^## |\Z)',
        markdown_text,
        flags=re.DOTALL | re.MULTILINE
    )

    if not match:
        return []

    heading = match.group(1).strip()
    body = match.group(2).strip()

    recitals = re.findall(
        r'(- \(\d+\).*?)(?=\n- \(\d+\)|\Z)',
        body,
        flags=re.DOTALL
    )

    chunks = []
    # title block chunk
    chunks.append({
        "doc_id": "eu_ai_act_001",
        "chunk_id": "eu_ai_act_001_title_block",
        "section_type": "title_block",
        "section_label": "title_block",
        "source_file": "eu_ai_act_001.pdf",
        "text": title_block(markdown_text)
    })

    for i in range(0, len(recitals), group_size):
        group = recitals[i:i + group_size]
        start_num = i + 1
        end_num = i + len(group)

        chunk_text = heading + "\n\n" + "\n\n".join(group)



        chunks.append({
            "doc_id": "eu_ai_act_001",
            "chunk_id": f"eu_ai_act_001_recitals_{start_num}_{end_num}",
            "section_type": "recitals",
            "section_label": f"{start_num}_{end_num}",
            "source_file": "eu_ai_act_001.pdf",
            "text": chunk_text
        })

    return chunks


if __name__ == "__main__":
    md_path = Path("data/processed/eu_ai_act_001/parsed.md")
    output_path = Path("data/chunks/eu_ai_act_001_chunks.json")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    text = md_path.read_text(encoding="utf-8")
    chunks = split_recitals(text, group_size=4)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(chunks)} chunks to {output_path}")