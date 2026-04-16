# AI Governance and Open-Model Compliance — RAG System

A portfolio project that builds a Retrieval-Augmented Generation (RAG) assistant over three AI governance and compliance documents. Ask natural-language questions and get source-grounded answers with citations.

---

## Why this domain?

AI governance is a fast-moving space where practitioners need to quickly locate obligations, risk definitions, and security controls scattered across long regulatory and guidance documents. A RAG system is a natural fit: it retrieves the relevant passage before generating an answer, so responses stay grounded in the actual text rather than model memorisation.

---

## Architecture

```
Raw PDFs
   │
   ▼
parse_docs.py          (PDF → Markdown via marker-pdf)
   │
   ▼
chunks_docs.py         EU AI Act  ─┐
nist_genai_profile.py  NIST        ├─► per-doc JSON chunk files
ncsc.py                NCSC       ─┘
   │
   ▼
build_chunk_corpus.py  (merge all chunk files → all_chunks.json)
   │
   ▼
validate_chunks.py     (schema check, dedup, length filter → all_chunks_clean.json)
   │
   ▼
embed_chunks_qdrant.py (BAAI/bge-base-en-v1.5 → local Qdrant collection)
   │
   ▼
ask_bedrock.py         (question → retrieve top-k → Bedrock Converse → answer)
```

---

## Corpus

| Document | ID | Chunks | Notes |
|---|---|---|---|
| EU AI Act (Regulation 2024/1689) | `eu_ai_act_001` | 188 | Recitals, 114 articles, 8 annexes |
| NIST Generative AI Profile (AI 600-1) | `nist_genai_ai_profile_001` | 67 | RMF subcategories split per GOVERN/MAP/MEASURE/MANAGE |
| NCSC Guidelines for Secure AI System Development | `ncsc_secure_ai_001` | 23 | Duplicate outline entries and bibliography noise removed |

**Total indexed: 274 chunks** (title blocks and reference-only entries excluded from the vector index)

---

## Chunking strategy

**EU AI Act** — Three-level split:
- *Recitals*: size-aware grouping (≤ 5,000 chars per group)
- *Articles*: each article gets its own chunk (`## Article N` + subject heading + body); large articles are split on paragraph boundaries
- *Annexes*: each annex is one chunk, split by size if needed

**NIST GenAI Profile** — Section-level split, with automatic expansion of any section that contains RMF subcategory headings (`GOVERN N.N:`, `MAP N.N:`, etc.) into one chunk per subcategory. This covers both Section 3 and Appendix A.

**NCSC** — Heading-level split with three filters applied:
1. Skip-list for front matter (Contents, About this document, etc.)
2. Duplicate label resolution — the outline summary pass and the full-content pass produce the same four section headings; the longer version is kept
3. "Further reading" bibliography entries are dropped entirely

---

## Setup

```bash
# 1. Clone and enter the project
git clone <repo-url>
cd "AI governance and open-model compliance"

# 2. Create and activate virtual environment
python -m venv .venv
.venv/Scripts/activate        # Windows
# source .venv/bin/activate   # Mac/Linux

# 3. Install dependencies
pip install sentence-transformers qdrant-client boto3 python-dotenv groq

# 4. Copy .env.example to .env and fill in credentials
cp .env.example .env
```

`.env.example`:
```
GROQ_API_KEY=your_groq_api_key_here
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_key_id
AWS_SECRET_ACCESS_KEY=your_secret_key
```

---

## Running the pipeline

```bash
# Step 1 – chunk each document (already done; re-run if sources change)
python scripts/chunks_docs.py
python scripts/nist_genai_profile.py
python scripts/ncsc.py

# Step 2 – merge and validate
python scripts/build_chunk_corpus.py
python scripts/validate_chunks.py

# Step 3 – embed and index
python scripts/embed_chunks_qdrant.py

# Step 4 – ask a question (Bedrock / Nova Lite)
python scripts/ask_bedrock.py

# Step 4 (alt) – ask a question (Groq / Llama)
python scripts/ask.py

# Step 5 – run retrieval evaluation
python scripts/evaluate_rag.py
```

---

## Asking questions

```
$ python scripts/ask_bedrock.py
Enter your question: What obligations apply to providers of high-risk AI systems?

=== RETRIEVED CHUNKS ===

Rank 1
Score: 0.876
doc_id: eu_ai_act_001
chunk_id: eu_ai_act_001_article_16
section_label: Article 16 – Obligations of providers of high-risk AI systems
text preview: ...

=== FINAL ANSWER ===

According to Chunk 1 (Article 16), providers of high-risk AI systems must: ensure
the system complies with requirements in Chapter III Section 2, draw up technical
documentation, keep logs, affix CE marking...

Sources:
- eu_ai_act_001 | eu_ai_act_001_article_16 | Article 16 – Obligations of providers...
```

---

## Generation model

| Setting | Value |
|---|---|
| Provider | Amazon Bedrock |
| Model | `amazon.nova-lite-v1:0` |
| Auth | Long-term IAM credentials (AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY) |
| Region | `us-east-1` |
| API | Bedrock Converse API (`boto3`) |
| Max tokens | 1,000 |
| Temperature | 0.1 |

An alternative Groq path (`ask.py`, `llama-3.1-8b-instant`) is also included for offline or API-key-only use.

---

## Retrieval evaluation

Evaluated on 15 hand-written questions covering all three source families.

| Metric | Score |
|---|---|
| Top-1 accuracy | 93% (14/15) |
| Top-3 accuracy | 93% (14/15) |
| Top-5 accuracy | 93% (14/15) |

The one miss ("monitoring and operation" for NCSC) is caused by query-vocabulary drift — the NCSC section title uses "operation and maintenance" while the query uses "monitoring". This is a known limitation of dense-only retrieval with no query expansion.

Run `python scripts/evaluate_rag.py` to reproduce these results. Detailed per-question output is saved to `data/eval/rag_eval_results.json`.

---

## Known limitations

- **Single-stage dense retrieval only** — no re-ranking, no hybrid BM25+dense. Vocabulary mismatches can cause misses (see NCSC monitoring result above).
- **No answer evaluation** — the eval script measures retrieval accuracy, not answer quality. LLM-as-judge or reference answer comparison would be needed for end-to-end evaluation.
- **Small corpus** — three documents. Adding more sources (e.g. ISO 42001, OECD AI Principles) would improve coverage.
- **Chunk size not uniform** — some EU AI Act articles are long and split by paragraph heuristic, which may break mid-argument.
- **Local Qdrant** — uses the embedded SQLite-backed Qdrant. Not suitable for concurrent access or large-scale deployment.

---

## Next improvements

- [ ] Add BM25 hybrid retrieval and fuse scores with RRF
- [ ] Add a re-ranker (e.g. cross-encoder) between retrieval and generation
- [ ] Expand corpus (ISO 42001, OECD AI Principles, UK AI Safety Institute guidance)
- [ ] Add reference answers to evaluation questions and score generation quality
- [ ] Build a simple Streamlit or Gradio UI

---

## Project structure

```
configs/          source lists and document type config
data/
  chunks/         per-doc and merged chunk JSON files
  eval/           evaluation questions and results
  logs/           RAG run logs (JSONL)
  manifests/      index and validation reports
  processed/      parsed Markdown from PDFs
  raw/            original PDF documents
  vector_store/   local Qdrant database
docs/             design notes and chunking documentation
eval/             earlier retrieval-only eval script (superseded by scripts/evaluate_rag.py)
scripts/          all pipeline and query scripts
```
