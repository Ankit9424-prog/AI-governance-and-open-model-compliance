import json
import os
from datetime import datetime, timezone
from pathlib import Path

from groq import Groq
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

QDRANT_PATH = "data/vector_store/qdrant"
COLLECTION_NAME = "ai_governance_chunks"
EMBED_MODEL_NAME = "BAAI/bge-base-en-v1.5"
LLM_MODEL_NAME = "llama-3.1-8b-instant"

TOP_K_RETRIEVE = 8
TOP_K_CONTEXT = 4

LOG_PATH = Path("data/logs/rag_runs.jsonl")


def retrieve_chunks(question, embed_model, qdrant_client, top_k=TOP_K_RETRIEVE):
    query_vector = embed_model.encode(
        [question],
        normalize_embeddings=True,
        convert_to_numpy=True,
    )[0]

    hits = qdrant_client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector.tolist(),
        limit=top_k,
    ).points

    chunks = []
    for hit in hits:
        payload = hit.payload or {}
        chunks.append(
            {
                "score": float(hit.score),
                "doc_id": payload.get("doc_id"),
                "chunk_id": payload.get("chunk_id"),
                "section_type": payload.get("section_type"),
                "section_label": payload.get("section_label"),
                "text": payload.get("text", ""),
            }
        )

    return chunks


def select_context_chunks(question, chunks, top_k=TOP_K_CONTEXT):
    q = question.lower()

    if "nist" in q:
        nist_chunks = [c for c in chunks if "nist" in (c.get("doc_id") or "").lower()]
        return nist_chunks[:top_k] if nist_chunks else chunks[:top_k]

    if "eu ai act" in q or "eu ai" in q:
        eu_chunks = [c for c in chunks if "eu_ai_act" in (c.get("doc_id") or "").lower()]
        return eu_chunks[:top_k] if eu_chunks else chunks[:top_k]

    if "ncsc" in q:
        ncsc_chunks = [c for c in chunks if "ncsc" in (c.get("doc_id") or "").lower()]
        return ncsc_chunks[:top_k] if ncsc_chunks else chunks[:top_k]

    return chunks[:top_k]


def build_context(chunks):
    parts = []

    for i, chunk in enumerate(chunks, start=1):
        parts.append(
            f"[Chunk {i}]\n"
            f"doc_id: {chunk['doc_id']}\n"
            f"chunk_id: {chunk['chunk_id']}\n"
            f"section_type: {chunk['section_type']}\n"
            f"section_label: {chunk['section_label']}\n"
            f"text:\n{chunk['text']}\n"
        )

    return "\n\n".join(parts)


def format_sources(chunks):
    seen = set()
    lines = []

    for chunk in chunks:
        line = f"- {chunk['doc_id']} | {chunk['chunk_id']} | {chunk['section_label']}"
        if line not in seen:
            lines.append(line)
            seen.add(line)

    return "\n".join(lines)


def generate_answer(question, context):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY is not set in your environment.")

    client = Groq(api_key=api_key)

    system_prompt = """
You are a careful RAG assistant for AI governance and compliance documents.

Rules:
- Answer only from the provided context.
- Do not use outside knowledge.
- If the context is insufficient, say so clearly.
- Be precise and concise.
""".strip()

    user_prompt = f"""
Question:
{question}

Context:
{context}

Instructions:
- Answer the question directly.
- Use multiple relevant chunks when available.
- Do not invent details.
""".strip()

    response = client.chat.completions.create(
        model=LLM_MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.1,
    )

    return response.choices[0].message.content


def save_log(question, retrieved_chunks, context_chunks, answer):
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    record = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "question": question,
        "retrieved_chunks": retrieved_chunks,
        "context_chunks": context_chunks,
        "answer": answer,
        "embedding_model": EMBED_MODEL_NAME,
        "llm_model": LLM_MODEL_NAME,
        "collection_name": COLLECTION_NAME,
    }

    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def main():
    question = input("Enter your question: ").strip()
    if not question:
        print("Question cannot be empty.")
        return

    embed_model = SentenceTransformer(EMBED_MODEL_NAME)
    qdrant_client = QdrantClient(path=QDRANT_PATH)

    try:
        retrieved_chunks = retrieve_chunks(question, embed_model, qdrant_client)

        if not retrieved_chunks:
            print("No chunks retrieved.")
            return

        context_chunks = select_context_chunks(question, retrieved_chunks)
        context = build_context(context_chunks)
        answer = generate_answer(question, context)
        sources = format_sources(context_chunks)

        print("\n=== RETRIEVED CHUNKS ===")
        for i, chunk in enumerate(context_chunks, start=1):
            preview = chunk["text"].replace("\n", " ")[:250]
            print(f"\nRank {i}")
            print("Score:", chunk["score"])
            print("doc_id:", chunk["doc_id"])
            print("chunk_id:", chunk["chunk_id"])
            print("section_label:", chunk["section_label"])
            print("text preview:", preview)

        print("\n=== FINAL ANSWER ===\n")
        print(answer)

        print("\nSources:")
        print(sources)

        save_log(question, retrieved_chunks, context_chunks, answer)
        print(f"\nRun logged to: {LOG_PATH}")

    finally:
        qdrant_client.close()


if __name__ == "__main__":
    main()