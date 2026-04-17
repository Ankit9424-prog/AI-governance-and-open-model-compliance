# AI Governance & Open-Model Compliance

A source-grounded Retrieval-Augmented Generation (RAG) project for answering questions about AI governance, security guidance, and model-compliance documents.

This repository is built as a portfolio-grade RAG system rather than a toy chatbot. It focuses on document parsing, structure-aware chunking, local vector search, hybrid retrieval, and grounded answer generation over real policy and guidance texts.

---

## What this project does

This project lets you ask natural-language questions such as:

- What obligations apply to providers under the EU AI Act?
- How does the NIST Generative AI Profile describe risk-management activities?
- What secure development practices are recommended by the NCSC guidance?

The system retrieves relevant passages from the indexed corpus first, then generates an answer from those retrieved chunks instead of relying on unsupported model recall.

---

## Why this project matters

AI governance documents are long, dense, and spread across multiple institutions. Important requirements are often buried inside recitals, articles, annexes, profiles, and guidance sections.

This project explores a practical question:

**How do you build a small but serious RAG system that can answer compliance questions with traceable evidence from the source documents?**

Instead of optimizing only for “chatbot feel,” the repo emphasizes:

- grounded retrieval
- transparent source usage
- chunking logic tailored to document structure
- reproducible local indexing
- a clean path from raw documents to an interactive UI

---

## Current indexed corpus

The active chunk corpus currently used by the application is built from three document families:

1. **EU AI Act**  
   Regulation-style content with recitals, articles, and annexes.

2. **NIST Generative AI Profile**  
   Governance and risk-management guidance organized around RMF-style categories.

3. **NCSC Guidelines for Secure AI System Development**  
   Security-focused guidance on building and maintaining AI systems safely.

The repository also includes a broader corpus manifest that tracks additional sources beyond the currently merged chunk corpus.

---

## Retrieval and generation design

The system uses a **hybrid retrieval pipeline**:

- **Dense retrieval** for semantic similarity
- **BM25 retrieval** for keyword matching
- **Reciprocal Rank Fusion (RRF)** to combine both rankings

This matters because governance queries often fail under dense-only retrieval when the user’s wording differs from the wording used in the source document. Hybrid retrieval improves robustness by combining semantic and lexical evidence.

After retrieval:

1. the top chunks are selected as context
2. context is formatted into a grounded prompt
3. a language model generates the answer
4. the UI shows both the answer and the source sections used

---

## High-level pipeline

```text
Raw documents
   ↓
Document parsing
   ↓
Document-specific chunking
   ↓
Merged chunk corpus
   ↓
Chunk validation / cleaning
   ↓
Embeddings
   ↓
Local Qdrant index
   ↓
Hybrid retrieval (Dense + BM25 + RRF)
   ↓
LLM answer generation
   ↓
CLI / Streamlit interface
```

---

## Project structure

```text
.
├── app.py
├── configs/
├── data/
│   ├── chunks/
│   │   ├── all_chunks.json
│   │   ├── all_chunks_clean.json
│   │   ├── eu_ai_act_001_chunks.json
│   │   ├── nist_genai_profile_001_chunks.json
│   │   └── ncsc_secure_ai_001_chunks.json
│   ├── manifests/
│   │   ├── chunk_validation_report.json
│   │   ├── corpus_manifest.csv
│   │   └── embedding_index_report.json
│   ├── raw/
│   └── vector_store/
├── docs/
│   ├── chunk_schema.md
│   ├── corpus_rules.md
│   └── scope.md
└── scripts/
    ├── ask.py
    ├── build_chunk_corpus.py
    ├── chunks_docs.py
    ├── embed_chunks_qdrant.py
    ├── ncsc.py
    ├── nist_genai_profile.py
    ├── parse_docs.py
    ├── retrieval.py
    └── validate_chunks.py
```

---

## Main components

### `app.py`
A Streamlit interface for interactive querying. It loads the chunk corpus, connects to the local Qdrant index, runs hybrid retrieval, and displays grounded answers with source sections.

### `scripts/retrieval.py`
Implements the hybrid retrieval logic:

- BM25 keyword search
- dense vector search
- Reciprocal Rank Fusion

This is one of the core files in the repo because it handles the retrieval behavior that determines answer quality.

### `scripts/ask.py`
A command-line version of the RAG workflow. Useful for quick testing, debugging, and logging runs without launching the Streamlit app.

### `scripts/parse_docs.py`
Parses raw source documents into processed text/markdown. This is the start of the document-preparation pipeline.

### `scripts/chunks_docs.py`
Creates structure-aware chunks for the EU AI Act, including recitals, articles, and annexes.

### `scripts/nist_genai_profile.py`
Creates chunks for the NIST Generative AI Profile, including RMF-style subcategory-aware chunking.

### `scripts/ncsc.py`
Creates chunks for the NCSC secure AI guidance while removing unwanted front matter and bibliography-style noise.

### `scripts/build_chunk_corpus.py`
Merges per-document chunk files into a single corpus file.

### `scripts/validate_chunks.py`
Cleans and validates the chunk corpus before indexing.

### `scripts/embed_chunks_qdrant.py`
Embeds the cleaned chunks and writes them into a local Qdrant collection.

---

## Quick start

### 1. Clone the repository

```bash
git clone https://github.com/Ankit9424-prog/AI-governance-and-open-model-compliance.git
cd AI-governance-and-open-model-compliance
```

### 2. Create a virtual environment

#### Windows (PowerShell)

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
```

#### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

There is no pinned `requirements.txt` in the repository right now, so install the packages used by the current codebase:

```bash
pip install streamlit python-dotenv groq sentence-transformers qdrant-client rank-bm25 docling pypdfium2
```

### 4. Create a `.env` file

Add your Groq API key:

```env
GROQ_API_KEY=your_groq_api_key_here
```

---

## Run the project

### Option A: Launch the Streamlit app

```bash
streamlit run app.py
```

### Option B: Use the CLI

```bash
python scripts/ask.py
```

---

## Rebuild the corpus and index from scratch

Run the full pipeline in this order:

```bash
python scripts/parse_docs.py
python scripts/chunks_docs.py
python scripts/nist_genai_profile.py
python scripts/ncsc.py
python scripts/build_chunk_corpus.py
python scripts/validate_chunks.py
python scripts/embed_chunks_qdrant.py
```

Then launch the app:

```bash
streamlit run app.py
```

---

## Example questions

Try questions like these:

```text
What obligations apply to providers of high-risk AI systems?
How does the NIST Generative AI Profile organize governance activities?
What does the NCSC guidance recommend for secure AI system development?
What kinds of risk-management expectations appear across these sources?
How do the EU AI Act and NIST guidance differ in tone and structure?
```

---

## What makes this repo more than a basic tutorial

This project goes beyond a standard “upload a PDF and chat with it” workflow in a few ways:

- **document-specific chunking**
  - the chunking logic is customized per source instead of applying one generic splitter to everything

- **hybrid retrieval**
  - lexical and semantic retrieval are combined instead of relying on a single search method

- **local-first indexing**
  - the vector store is local, which keeps experimentation lightweight and reproducible

- **source-grounded answers**
  - the interface exposes which document sections were used

- **clear preprocessing pipeline**
  - raw documents, processed text, chunk corpora, manifests, and vector index are all separated

---

## Current limitations

- The active indexed corpus is still relatively small.
- The project does not yet include a dedicated reranker stage.
- Context selection after retrieval is still rule-based in places.
- Dependency installation is manual because a pinned environment file is not included yet.
- The broader corpus manifest contains additional sources that are not yet part of the active merged chunk corpus.

---

## Good next improvements

If you want to extend the project further, strong next steps would be:

1. add a `requirements.txt` or `pyproject.toml`
2. add automated retrieval evaluation
3. add answer-quality evaluation
4. add reranking after retrieval
5. expand the indexed corpus
6. improve citation formatting in the UI
7. package the pipeline for easier reproducibility

---

## Who this project is for

This repository is especially useful if you are interested in:

- RAG engineering
- LLM application development
- AI governance and compliance
- document intelligence
- hybrid retrieval systems
- portfolio projects for ML / AI engineering roles

---

## Summary

This is a practical RAG system for AI governance and open-model compliance work. It combines document-aware chunking, local vector search, hybrid retrieval, and a simple user interface to answer questions with grounded evidence from real governance and security documents.
