"""
app.py — Streamlit UI for the AI Governance RAG assistant

Run with:
    streamlit run app.py
"""

import os
import sys
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from groq import Groq
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

# ── make sure scripts/ is importable ─────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent / "scripts"))
from retrieval import hybrid_search, load_chunks  # noqa: E402

load_dotenv()

# ── constants ─────────────────────────────────────────────────────────────────
QDRANT_PATH = "data/vector_store/qdrant"
EMBED_MODEL_NAME = "BAAI/bge-base-en-v1.5"
LLM_MODEL_NAME = "llama-3.1-8b-instant"
TOP_K_RETRIEVE = 8
TOP_K_CONTEXT = 4

DOC_LABELS = {
    "eu_ai_act_001": "EU AI Act",
    "nist_genai_ai_profile_001": "NIST GenAI Profile",
    "ncsc_secure_ai_001": "NCSC Secure AI",
}

# ── cached resource loading ───────────────────────────────────────────────────

@st.cache_resource(show_spinner="Loading embedding model…")
def get_embed_model():
    return SentenceTransformer(EMBED_MODEL_NAME)


@st.cache_resource(show_spinner="Connecting to vector store…")
def get_qdrant():
    return QdrantClient(path=QDRANT_PATH)


@st.cache_data(show_spinner="Loading chunk corpus…")
def get_all_chunks():
    return load_chunks()


# ── generation ────────────────────────────────────────────────────────────────

def build_context(chunks: list[dict]) -> str:
    parts = []
    for i, chunk in enumerate(chunks, start=1):
        parts.append(
            f"[Chunk {i}]\n"
            f"doc_id: {chunk['doc_id']}\n"
            f"chunk_id: {chunk['chunk_id']}\n"
            f"section_label: {chunk['section_label']}\n"
            f"text:\n{chunk['text']}\n"
        )
    return "\n\n".join(parts)


def select_context_chunks(question: str, chunks: list[dict], top_k: int = TOP_K_CONTEXT) -> list[dict]:
    q = question.lower()
    if "nist" in q:
        filtered = [c for c in chunks if "nist" in (c.get("doc_id") or "").lower()]
        return filtered[:top_k] if filtered else chunks[:top_k]
    if "eu ai act" in q or "eu ai" in q:
        filtered = [c for c in chunks if "eu_ai_act" in (c.get("doc_id") or "").lower()]
        return filtered[:top_k] if filtered else chunks[:top_k]
    if "ncsc" in q:
        filtered = [c for c in chunks if "ncsc" in (c.get("doc_id") or "").lower()]
        return filtered[:top_k] if filtered else chunks[:top_k]
    return chunks[:top_k]


def generate_answer(question: str, context: str) -> str:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return "Error: GROQ_API_KEY is not set in your .env file."

    client = Groq(api_key=api_key)

    system_prompt = (
        "You are a careful RAG assistant for AI governance and compliance documents.\n\n"
        "Rules:\n"
        "- Answer ONLY using information from the provided context.\n"
        "- Do not use outside knowledge.\n"
        "- If the context is insufficient, say so clearly.\n"
        "- Be precise and concise.\n"
        "- When citing, mention which chunk (e.g. 'According to Chunk 1...')."
    )

    user_prompt = (
        f"Question:\n{question}\n\n"
        f"Context:\n{context}\n\n"
        "Instructions:\n"
        "- Answer directly using only the context above.\n"
        "- Do not invent details.\n"
        "- If context is insufficient, say so."
    )

    response = client.chat.completions.create(
        model=LLM_MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.1,
    )
    return response.choices[0].message.content


# ── Streamlit page ────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="AI Governance RAG",
    page_icon="📋",
    layout="wide",
)

st.title("📋 AI Governance RAG Assistant")
st.caption(
    "Ask questions about the **EU AI Act**, **NIST GenAI Profile**, or **NCSC Secure AI** guidelines. "
    "Answers are grounded in the source documents."
)

# load resources once (cached after first load)
embed_model = get_embed_model()
qdrant_client = get_qdrant()
all_chunks = get_all_chunks()

# ── question input ─────────────────────────────────────────────────────────────
with st.form("question_form"):
    question = st.text_input(
        "Your question",
        placeholder="e.g. What obligations apply to providers of high-risk AI systems?",
    )
    submitted = st.form_submit_button("Ask", type="primary")

if not submitted or not question.strip():
    st.stop()

question = question.strip()

# ── retrieval ─────────────────────────────────────────────────────────────────
with st.spinner("Retrieving relevant chunks…"):
    retrieved = hybrid_search(question, embed_model, qdrant_client, all_chunks, top_k=TOP_K_RETRIEVE)

if not retrieved:
    st.warning("No relevant chunks found.")
    st.stop()

context_chunks = select_context_chunks(question, retrieved)
context = build_context(context_chunks)

# ── generation ────────────────────────────────────────────────────────────────
with st.spinner("Generating answer…"):
    answer = generate_answer(question, context)

# ── answer ────────────────────────────────────────────────────────────────────
st.subheader("Answer")
st.markdown(answer)

# ── sources ───────────────────────────────────────────────────────────────────
st.subheader("Sources")
seen = set()
for chunk in context_chunks:
    key = chunk["chunk_id"]
    if key in seen:
        continue
    seen.add(key)
    doc_label = DOC_LABELS.get(chunk["doc_id"], chunk["doc_id"])
    st.markdown(f"**{doc_label}** — {chunk['section_label']}")

# ── retrieved chunks detail (collapsible) ─────────────────────────────────────
with st.expander("Retrieved chunks (debug view)"):
    for i, chunk in enumerate(context_chunks, start=1):
        doc_label = DOC_LABELS.get(chunk["doc_id"], chunk["doc_id"])
        st.markdown(f"**Rank {i} · {doc_label} · RRF score: {chunk.get('rrf_score', 'n/a')}**")
        st.markdown(f"*{chunk['section_label']}*")
        st.text(chunk["text"][:600] + ("…" if len(chunk["text"]) > 600 else ""))
        st.divider()
