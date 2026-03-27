# Corpus Rules

## Purpose
These rules define which documents are allowed into the corpus for the AI governance and open-model compliance RAG project. The goal is to keep the dataset trustworthy, relevant, and structured enough for later retrieval, chunking, and citation.

## Include a document if it:
- comes from an official or primary source
- is directly relevant to AI governance, model compliance, AI risk, AI security, model documentation, or model licensing
- has clear provenance, including a source URL and publisher
- is stable enough to cite later
- contains meaningful technical, legal, or policy content
- has enough structure to support parsing, such as headings, sections, tables, clauses, or lists

## Preferred source types
- official regulations
- official policy documents
- official AI governance frameworks
- official security guidance for AI systems
- official model cards
- official license or terms-of-use documents
- official technical whitepapers directly related to governance or compliance

## Reject a document if it:
- is a blog post, summary article, or opinion piece
- is a news article describing another source
- is a Reddit post, forum post, or social media thread
- is mostly marketing material
- has unclear authorship or weak provenance
- is a duplicate or unofficial mirror of a document already collected
- is too far outside the project scope
- is badly corrupted, unreadable, or impossible to verify

## Relevance rules
A document should stay in the corpus only if it supports at least one of these use cases:
- answering questions about AI regulation or compliance obligations
- answering questions about AI risk-management frameworks
- answering questions about model limitations, intended use, or safety notes
- answering questions about license restrictions, permissions, or usage conditions
- answering questions about governance-related technical guidance

## Source quality rules
- prefer official publisher websites over third-party reposts
- preserve the original source URL whenever possible
- record the publisher name
- record the version or effective date if available
- avoid collecting multiple copies of the same document unless versions differ meaningfully

## Versioning rules
- keep the newest official version by default
- keep older versions only if version comparison may matter later
- if multiple versions are kept, they must have separate document IDs
- note version differences in the manifest when possible

## Duplicate handling rules
A document counts as a duplicate if:
- the content is the same document from a different mirror
- the same file has already been downloaded before
- the document title and content clearly match an existing entry

When duplicates are found:
- keep the official source version
- mark the duplicate in notes if needed
- do not index both copies unless there is a clear reason

## Parsing suitability rules
Before a document is accepted for later indexing, it should be checked for:
- readable text extraction
- preserved section hierarchy
- acceptable reading order
- tables that remain interpretable
- limited boilerplate noise such as repeated headers or footers

A document may remain in the raw corpus even if parsing is difficult, but it should be flagged for review.

## Excluded content categories
- general AI news
- informal commentary
- unrelated machine learning tutorials
- generic software documentation not tied to governance or compliance
- low-authority summaries of laws or licenses
- documents with no clear citation value

## Final decision rule
If a document is not clearly useful for grounded question answering in this project, it should not be included.