# AI Governance and Open-Model Compliance RAG

A portfolio-grade Retrieval-Augmented Generation (RAG) project focused on **AI governance, regulatory compliance, security guidance, and open-model documentation**. This project aims to build a practical system that can retrieve and later answer questions from complex real-world documents such as regulations, frameworks, model cards, licenses, and security guidance.

---

## Overview

Most beginner RAG projects use clean text files and simple chunking. This project is different because it focuses on **messy, high-value documents** that are much closer to real production use cases.

The main goal is to build a system that can:

- parse complex documents properly
- chunk them in a meaningful way
- store them for semantic retrieval
- evaluate retrieval quality
- later support grounded answer generation

This project is being developed as a **strong portfolio piece** to demonstrate practical understanding of:

- document parsing
- chunking strategy
- vector databases
- retrieval engineering
- evaluation of RAG pipelines

---

## Problem Statement

RAG systems often fail not because the LLM is weak, but because the **retrieval pipeline is poor**. If the system cannot parse documents well, preserve structure, or retrieve the right chunk, the final answer will also be weak.

This project addresses those issues by focusing on:

- layout-aware parsing instead of plain text extraction
- document-specific chunking instead of naive fixed splitting
- metadata-rich chunk storage
- dense retrieval experiments using embeddings
- evaluation of retrieval quality before full answer generation

---

## Project Goals

The main goals of this project are:

1. Build a clean and reusable RAG pipeline for governance and compliance documents.
2. Handle difficult real-world PDFs and structured documents.
3. Improve retrieval quality through better chunking and metadata.
4. Evaluate dense retrieval performance using real queries.
5. Extend the project later with hybrid retrieval, reranking, and grounded generation.

---

## Domain Focus

This project focuses on the niche of **AI governance and open-model compliance**.

This includes documents such as:

- regulations
- risk management frameworks
- security guidance
- model cards
- open-model licenses and terms
- AI policy and governance documentation

This domain was chosen because it is:

- practical
- technically interesting
- relevant to modern AI systems
- difficult enough to go beyond tutorial-level RAG

---

## Current Corpus

The current corpus includes documents such as:

- **EU AI Act**
- **NIST AI RMF / Generative AI Profile**
- **NCSC Guidelines for Secure AI System Development**
- **Gemma model card and terms**
- other governance and compliance-related documents

These documents represent multiple document types, including:

- `regulation`
- `framework`
- `security_guidance`
- `model_card`
- `license`

---

## Tech Stack

- **Python**
- **Docling** for parsing PDFs and document conversion
- **Qdrant** for local vector storage
- **Sentence Transformers** for embeddings
- **JSON / CSV** for chunk and manifest storage
- **Jupyter Notebook / Python scripts** for experimentation and evaluation

---

## Project Structure

```text
AI-governance-and-open-model-compliance/
│
├── configs/
├── data/
│   ├── raw/
│   ├── processed/
│   ├── chunks/
│   └── manifests/
├── docs/
├── scripts/
├── notebooks/
└── README.md
```

---

## Pipeline Overview

### 1. Source Collection

Relevant governance, compliance, and security documents are collected from official or high-quality public sources and tracked in a manifest.

The source manifest is used to store information such as:

- document title
- source URL
- publisher
- document type
- jurisdiction
- local file path
- parsing status

This makes the corpus easier to manage and extend later.

---

### 2. Parsing

The documents are parsed using **Docling** into markdown and plain text.

The parsing stage is designed to be lightweight and practical. I disabled some expensive features such as OCR and table-structure extraction in some experiments to keep the pipeline faster and easier to run locally.

The main goal at this stage is to convert raw files into usable structured text while preserving as much meaning as possible.

---

### 3. Chunking

One of the most important parts of this project is **chunking**.

Instead of using only simple fixed-size chunking, I explored **document-aware chunking strategies**, because different documents have different structures.

Examples include:

- splitting by headings
- grouping related EU AI Act recitals together
- chunking NIST sections by section headers
- keeping meaningful section labels in metadata
- removing unnecessary title blocks or front matter where needed

The idea is that better chunking leads to better retrieval quality.

---

### 4. Corpus Building

After chunking individual documents, the outputs are cleaned and merged into a unified chunk corpus.

This stage includes:

- loading chunk files from multiple documents
- validating chunk structure
- removing duplicates if needed
- saving a combined chunk file for downstream retrieval

This makes retrieval experiments easier because all chunks are stored in one consistent format.

---

### 5. Dense Retrieval

Dense retrieval is the current main retrieval approach in the project.

At this stage, the workflow is:

1. load chunked text
2. generate embeddings
3. store vectors in Qdrant
4. run semantic search against the vector database
5. inspect top-k retrieved results

The purpose is to check whether semantic retrieval can find the correct document or section for a given query.

---

### 6. Evaluation

Retrieval quality is being evaluated using a set of manually written test queries.

The current evaluation focuses on whether the correct document appears in:

- Top-1
- Top-3
- Top-5 results

This helps measure whether the chunking and embedding pipeline is actually working.

Rather than jumping directly to generation, I am treating retrieval as the main engineering problem first.

---

## Why This Project Matters

This project matters because many RAG demos look good on the surface but are weak underneath. They often skip difficult steps such as document structure handling, chunk quality, and proper evaluation.

This project tries to be more realistic by focusing on:

- difficult real-world documents
- retrieval quality before generation
- metadata-aware chunking
- transparent corpus structure
- measurable evaluation

That makes it a stronger learning project and a better portfolio project.

---

## Example Questions the System Should Answer

Here are some example questions this system is designed to support:

- What obligations apply to providers of general-purpose AI models under the EU AI Act?
- How does the EU AI Act describe general-purpose AI models?
- How does NIST recommend managing generative AI risks?
- What secure development guidance is given for AI systems?
- What restrictions or permissions are described in open-model licenses?
- What governance requirements are relevant to AI compliance?

---

## Current Progress

So far, I have completed the following parts of the project:

- selected the domain and project scope
- collected initial source documents
- created source manifests
- parsed documents into markdown and text using Docling
- experimented with multiple chunking approaches
- built chunk outputs for several documents
- merged chunk outputs into a combined corpus
- started dense retrieval experiments with embeddings and Qdrant
- ran initial retrieval evaluation on a small query set

This means the project has moved beyond planning and into a working retrieval pipeline.

---

## Current Results

Initial dense retrieval evaluation on a small test set has shown promising results, including strong Top-3 and Top-5 accuracy in early experiments.

These results are still preliminary, and the system is still being improved. The current focus is not on claiming final performance, but on understanding where retrieval works and where it fails.

---

## Key Learnings So Far

Through this project, I have learned several important lessons about RAG systems:

- parsing quality affects everything downstream
- chunking strategy matters a lot for retrieval quality
- different document types often need different preprocessing logic
- metadata helps make retrieval more meaningful
- evaluation is necessary to know whether the system is actually improving
- real-world RAG is much more about retrieval engineering than just calling an LLM

---

## Challenges

Some of the main challenges in this project include:

- handling large and messy PDFs
- preserving useful structure during parsing
- avoiding overly large chunks
- designing chunking rules that fit different document styles
- keeping the pipeline fast enough for local experimentation
- making retrieval interpretable and easy to debug

These challenges are exactly what make the project valuable as a learning experience.

---

## Future Work

Planned next steps for the project include:

- improving chunk quality further
- fixing remaining large-chunk issues
- completing the embedding pipeline cleanly
- adding **hybrid retrieval** with BM25 + dense search
- adding **cross-encoder reranking**
- expanding the evaluation query set
- adding answer generation on top of retrieval
- building a small interface for querying the system
- creating benchmark reports and better documentation

---

## Long-Term Vision

The long-term goal is to turn this into a more complete compliance-focused RAG system that can:

- retrieve more accurately from complex documents
- provide grounded responses
- show citations to source sections
- support comparison across regulatory and guidance documents
- serve as a strong portfolio project for AI/ML or LLM engineering roles

---

## Status

**Current status: In Progress**

The current focus is on improving retrieval quality and finishing the retrieval pipeline before moving fully into answer generation.

---

## Author

**Ankit Katwal**

This project is being built as part of my learning journey in AI, machine learning, and LLM engineering.

---

## Resume Summary

Built a Retrieval-Augmented Generation (RAG) pipeline for AI governance and compliance documents using Docling, hierarchical chunking, Qdrant, and embedding-based retrieval. Processed complex PDFs into searchable chunks and evaluated retrieval performance to improve document grounding and retrieval quality.
