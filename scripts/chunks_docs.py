import re
import json
from pathlib import Path


# ── helpers ──────────────────────────────────────────────────────────────────

def _char_limit(n_chars, max_chars=6000):
    """Return True if text needs splitting (rough heuristic: ~250 chars/100 tokens)."""
    return n_chars > max_chars


def _split_by_size(text, chunk_size=5000):
    """Split a long text on paragraph boundaries, targeting ~chunk_size chars."""
    paragraphs = re.split(r'\n\n+', text.strip())
    parts, current = [], []
    current_len = 0
    for para in paragraphs:
        if current_len + len(para) > chunk_size and current:
            parts.append("\n\n".join(current))
            current, current_len = [], 0
        current.append(para)
        current_len += len(para)
    if current:
        parts.append("\n\n".join(current))
    return parts


# ── title block ───────────────────────────────────────────────────────────────

def title_block(markdown_text):
    match = re.search(r"(?s)\A(.*?)(?=\n##\s*Whereas:)", markdown_text,
                      flags=re.DOTALL | re.MULTILINE)
    return match.group(1).strip() if match else ""


# ── recitals ──────────────────────────────────────────────────────────────────

def split_recitals(markdown_text, max_chars=5000):
    """Group recitals by size rather than a fixed count."""
    match = re.search(
        r'(## Whereas:\s*)(.*?)(?=^## |\Z)',
        markdown_text,
        flags=re.DOTALL | re.MULTILINE,
    )
    if not match:
        return []

    heading = match.group(1).strip()
    body = match.group(2).strip()

    recitals = re.findall(
        r'(- \(\d+\).*?)(?=\n- \(\d+\)|\Z)',
        body,
        flags=re.DOTALL,
    )

    chunks = []
    group, group_len = [], 0
    group_start = 1

    for i, rec in enumerate(recitals, start=1):
        if group_len + len(rec) > max_chars and group:
            end = i - 1
            chunk_text = heading + "\n\n" + "\n\n".join(group)
            chunks.append({
                "doc_id": "eu_ai_act_001",
                "chunk_id": f"eu_ai_act_001_recitals_{group_start}_{end}",
                "section_type": "recitals",
                "section_label": f"Recitals {group_start}–{end}",
                "source_file": "eu_ai_act_001.pdf",
                "text": chunk_text,
            })
            group, group_len = [], 0
            group_start = i

        group.append(rec)
        group_len += len(rec)

    if group:
        end = len(recitals)
        chunk_text = heading + "\n\n" + "\n\n".join(group)
        chunks.append({
            "doc_id": "eu_ai_act_001",
            "chunk_id": f"eu_ai_act_001_recitals_{group_start}_{end}",
            "section_type": "recitals",
            "section_label": f"Recitals {group_start}–{end}",
            "source_file": "eu_ai_act_001.pdf",
            "text": chunk_text,
        })

    return chunks


# ── articles ──────────────────────────────────────────────────────────────────

def split_articles(markdown_text):
    """
    EU AI Act markdown structure inside each article:
        ## Article N
        ## Subject heading
        body text
    We join the article number + subject heading + body into one chunk,
    splitting large articles by paragraph boundaries.
    """
    # Capture: article heading, subject heading, body up to next ## heading
    pattern = re.compile(
        r'(?ms)'
        r'^(## Article\s+\d+[^\n]*)\n+'        # ## Article N  (group 1)
        r'^(## [^\n]+)\n+'                      # ## Subject heading  (group 2)
        r'(.*?)'                                # body  (group 3)
        r'(?=^## |\Z)'
    )

    chunks = []
    for m in pattern.finditer(markdown_text):
        article_heading = m.group(1).strip()
        subject_heading = m.group(2).strip()
        body = m.group(3).strip()

        # extract article number for stable IDs
        num_match = re.search(r'(\d+)', article_heading)
        art_num = num_match.group(1) if num_match else "x"

        label = re.sub(r'^## ', '', subject_heading)
        full_text = f"{article_heading}\n\n{subject_heading}\n\n{body}"

        if _char_limit(len(full_text)):
            parts = _split_by_size(f"{article_heading}\n\n{subject_heading}\n\n{body}")
            for j, part in enumerate(parts, start=1):
                chunks.append({
                    "doc_id": "eu_ai_act_001",
                    "chunk_id": f"eu_ai_act_001_article_{art_num}_p{j}",
                    "section_type": "article",
                    "section_label": f"Article {art_num} – {label}",
                    "source_file": "eu_ai_act_001.pdf",
                    "text": part,
                })
        else:
            chunks.append({
                "doc_id": "eu_ai_act_001",
                "chunk_id": f"eu_ai_act_001_article_{art_num}",
                "section_type": "article",
                "section_label": f"Article {art_num} – {label}",
                "source_file": "eu_ai_act_001.pdf",
                "text": full_text,
            })

    return chunks


# ── annexes ───────────────────────────────────────────────────────────────────

def split_annexes(markdown_text):
    """
    Annex pattern:  ## ANNEX <Roman>
                    ## optional subtitle
                    body
    """
    pattern = re.compile(
        r'(?ms)'
        r'^(## ANNEX\s+([IVX]+)[^\n]*)\n+'  # ## ANNEX I  (group 1, numeral in group 2)
        r'(.*?)'                              # body up to next annex or end  (group 3)
        r'(?=^## ANNEX\s+[IVX]+(?:\s|\Z)|\Z)'
    )

    chunks = []
    for m in pattern.finditer(markdown_text):
        annex_heading = m.group(1).strip()
        annex_id = m.group(2)              # exact roman numeral captured
        body = m.group(3).strip()
        if not body:
            continue
        label = re.sub(r'^## ', '', annex_heading)

        full_text = f"{annex_heading}\n\n{body}"

        if _char_limit(len(full_text)):
            parts = _split_by_size(full_text)
            for j, part in enumerate(parts, start=1):
                chunks.append({
                    "doc_id": "eu_ai_act_001",
                    "chunk_id": f"eu_ai_act_001_annex_{annex_id}_p{j}",
                    "section_type": "annex",
                    "section_label": f"Annex {annex_id}",
                    "source_file": "eu_ai_act_001.pdf",
                    "text": part,
                })
        else:
            chunks.append({
                "doc_id": "eu_ai_act_001",
                "chunk_id": f"eu_ai_act_001_annex_{annex_id}",
                "section_type": "annex",
                "section_label": f"Annex {annex_id}",
                "source_file": "eu_ai_act_001.pdf",
                "text": full_text,
            })

    return chunks


# ── main entry ────────────────────────────────────────────────────────────────

def chunk_eu_ai_act(markdown_text):
    chunks = []

    # 1. Title block (preamble before recitals)
    tb = title_block(markdown_text)
    if tb:
        chunks.append({
            "doc_id": "eu_ai_act_001",
            "chunk_id": "eu_ai_act_001_title_block",
            "section_type": "title_block",
            "section_label": "title_block",
            "source_file": "eu_ai_act_001.pdf",
            "text": tb,
        })

    # 2. Recitals (## Whereas: section)
    chunks.extend(split_recitals(markdown_text))

    # 3. Articles (## Article N + ## Subject + body)
    chunks.extend(split_articles(markdown_text))

    # 4. Annexes
    chunks.extend(split_annexes(markdown_text))

    return chunks


if __name__ == "__main__":
    md_path = Path("data/processed/eu_ai_act_001/parsed.md")
    output_path = Path("data/chunks/eu_ai_act_001_chunks.json")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    text = md_path.read_text(encoding="utf-8")
    chunks = chunk_eu_ai_act(text)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(chunks)} chunks to {output_path}")

    # breakdown by section_type
    from collections import Counter
    counts = Counter(c["section_type"] for c in chunks)
    for k, v in sorted(counts.items()):
        print(f"  {k}: {v}")
