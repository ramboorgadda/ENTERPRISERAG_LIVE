from __future__ import annotations
from sys import flags
from loguru import logger

from app.config import settings

from app.models import(
    ChatResponse,
    ResponseMetadata,
    RetrievedChunk,
    RetrievedChunkPreview
)

from app.security.spotlighting import build_spotlight_context
from app.security.system_prompt import build_system_prompt
from app.services.embedding_service import embed_texts
from app.services.llm_service import generate
from app.services.vector_store import search


def _retrieve(question: str, top_k: int = 5) -> list[RetrievedChunk]:
    embeddings = embed_texts([question])
    results = search(embeddings[0], top_k=top_k)
    chunks = [RetrievedChunk(text=r.text, source=r.source, score=r.score) for r in results]
    return chunks

def _generate(question: str, retrieved_chunks: list[RetrievedChunk]) -> ChatResponse:
    system_prompt = build_system_prompt()
    spotlight_context = build_spotlight_context(retrieved_chunks)
    user_msg = f"{spotlight_context}\n\nQuestion: {question}"
    raw = generate(system_prompt=system_prompt, user_prompt=user_msg)["text"]
    chunks_previews = [RetrievedChunkPreview(text=chunk.text, source=chunk.source, score=chunk.score) for chunk in retrieved_chunks]
    return ChatResponse(
        answer=raw,
        sources=[chunk.source for chunk in retrieved_chunks],
        confidence=1.0,
        metadata=ResponseMetadata(
            route = "rag",
            retrieved_chunks=chunks_previews),
    )
def _top_k_flags(flags: dict | int | None) -> int:
    if flags is None:
        return 5
    if isinstance(flags, int):
        return flags
    return flags.get("top_k", 5)
def run_rag(question: str, flags: dict | int | None = None) -> ChatResponse:
    top_k = _top_k_flags(flags)
    logger.info(f"Running Naive RAG with top_k={top_k}")
    retrieved_chunks = _retrieve(question, top_k=top_k)
    return _generate(question, retrieved_chunks)

def run_rag_with_trace(
    question: str, flags: dict | int | None = None
) -> tuple[ChatResponse, list[RetrievedChunk]]:
    top_k = _top_k_flags(flags)
    logger.info(f"Running Naive RAG with top_k={top_k}")
    retrieved_chunks = _retrieve(question, top_k=top_k)
    response = _generate(question, retrieved_chunks)
    return response, retrieved_chunks

run_rag_with_trace_no_cache = run_rag_with_trace