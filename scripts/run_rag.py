import os

from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient

try:
    from groq import Groq
except ImportError:
    Groq = None


MODEL_NAME = "BAAI/bge-base-en-v1.5"
QDRANT_PATH = "data/vector_store/qdrant"
COLLECTION_NAME = "ai_governance_chunks"
TOP_K = 3

# Start with False if you only want to test retrieval + context building.
USE_GROQ = False
GROQ_MODEL = "llama-3.1-8b-instant"

model = SentenceTransformer(MODEL_NAME)
client = QdrantClient(path=QDRANT_PATH)


def retrieve(query: str, top_k: int = TOP_K):
    query_vector = model.encode(
        [query],
        normalize_embeddings=True,
        convert_to_numpy=True,
    )[0]

    response = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector.tolist(),
        limit=top_k * 3,
        with_payload=True,
    )

    raw_hits = []
    for rank, hit in enumerate(response.points, start=1):
        payload = hit.payload or {}

        raw_hits.append(
            {
                "rank": rank,
                "score": hit.score,
                "doc_id": payload.get("doc_id", ""),
                "chunk_id": payload.get("chunk_id", ""),
                "section_label": payload.get("section_label", ""),
                "text": payload.get("text", ""),
            }
        )

    unique_hits = []
    seen_labels = set()
    seen_texts = set()

    for hit in raw_hits:
        label_key = (hit["doc_id"], hit["section_label"])
        text_key = hit["text"].strip()

        if label_key in seen_labels:
            continue
        if text_key in seen_texts:
            continue

        unique_hits.append(hit)
        seen_labels.add(label_key)
        seen_texts.add(text_key)

        if len(unique_hits) == top_k:
            break

    return unique_hits


def build_context(hits):
    parts = []

    for hit in hits:
        block = (
            f"Source {hit['rank']}\n"
            f"doc_id: {hit['doc_id']}\n"
            f"chunk_id: {hit['chunk_id']}\n"
            f"section_label: {hit['section_label']}\n"
            f"text: {hit['text']}"
        )
        parts.append(block)

    return "\n\n" + ("\n\n" + "-" * 60 + "\n\n").join(parts)

def print_context(hits):
    print("\n=== FINAL CONTEXT FOR LLM ===\n")

    for hit in hits:
        print(f"[{hit['doc_id']} | {hit['section_label']}]")
        print(hit["text"])
        print()

def show_best_hits(hits):
    print("\n=== BEST HITS ===\n")
    for hit in hits:
        print(f"{hit['rank']}. {hit['doc_id']} | {hit['section_label']} | score={hit['score']:.4f}")


def answer_with_groq(query: str, context: str):
    if Groq is None:
        raise ImportError(
            "Groq package is not installed. Run: pip install groq"
        )

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY is not set in your environment."
        )

    groq_client = Groq(api_key=api_key)

    prompt = f"""
Answer the question using only the context below.
If the answer is not clearly in the context, say:
"I do not have enough information in the retrieved context."

Question:
{query}

Context:
{context}
""".strip()

    completion = groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {
                "role": "system",
                "content": "You are a careful RAG assistant. Use only the provided context."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.0,
    )

    return completion.choices[0].message.content


def main():
    query = input("Ask: ").strip()

    if not query:
        print("No query entered.")
        client.close()
        return

    hits = retrieve(query, top_k=TOP_K)


    if not hits:
        print("No results found.")
        client.close()
        return

    print("\n=== RETRIEVED CHUNKS ===\n")
    for hit in hits:
        preview = hit["text"][:300].replace("\n", " ")
        print(f"{hit['rank']}. score={hit['score']:.4f}")
        print(f"   doc_id={hit['doc_id']}")
        print(f"   chunk_id={hit['chunk_id']}")
        print(f"   section_label={hit['section_label']}")
        print(f"   text={preview}")
        print()


    print_context(hits)
    show_best_hits(hits)
    context = build_context(hits)

    print("\n=== BUILT CONTEXT ===")
    print(context[:2000])  # print only the beginning so terminal stays readable

    if USE_GROQ:
        print("\n=== FINAL ANSWER ===\n")
        answer = answer_with_groq(query, context)
        print(answer)
    else:
        print("\nLLM step is OFF.")
        print("Set USE_GROQ = True after retrieval looks good.")

    client.close()


if __name__ == "__main__":
    main()