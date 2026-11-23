from __future__ import annotations

import uuid
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from app.config import settings
from app.models import RetrievedChunk

VECTOR_SIZE = 1536

def get_client() -> QdrantClient:
    return QdrantClient(url=settings.qdrant_url)

def ensure_collection() -> None:
    client = get_client()
    existing = {c.name for c in client.get_collections().collections}
    if settings.qdrant_collection not in existing:
        client.create_collection(
            collection_name=settings.qdrant_collection,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE)
        )
def upsert_chunks(chunks: list[RetrievedChunk], embeddings: list[list[float]]) -> None:
    ensure_collection()
    client = get_client()
    points = [
        PointStruct(
            id=str(uuid.uuid4()),
            vector=embedding,
            payload={"text": chunk.text, "source": chunk.source}
        )
        for chunk, embedding in zip(chunks, embeddings)
    ]
    client.upsert(
        collection_name=settings.qdrant_collection,
        points=points
    )


def search(query_embedding: list[float], top_k: int = 5) -> list[RetrievedChunk]:
    ensure_collection()
    client = get_client()
    if hasattr(client, "search"):
        response = client.search(
            collection_name=settings.qdrant_collection,
            query_vector=query_embedding,
            limit=top_k,
        )
    else:
        response_obj = client.query_points(
            collection_name=settings.qdrant_collection,
            query=query_embedding,
            limit=top_k,
        )
        response = getattr(response_obj, "points", response_obj)
    return [
        RetrievedChunk(
            text=hit.payload["text"],
            source=hit.payload["source"],
            score=hit.score,
        )
        for hit in response
    ]
def _build_sparse_index():
    from app.services.sparse_vector_service import SparseVectorIndex
    client = get_client()
    points, _ = client.scroll(collection_name=settings.qdrant_collection,
                                limit=10000,
                                with_payload=True,
                                with_vectors=False)
    documents = [
        {
            "text": point.payload["text"] if point.payload else None,
            "source": point.payload["source"] if point.payload else None,
            "id": point.id
        }
        for point in points
    ]
    sparse_index = SparseVectorIndex()
    sparse_index.fit(documents)
    return sparse_index

def sparse_search(query: str, top_k: int = 5) -> list[RetrievedChunk]:
    sparse_index = _build_sparse_index()
    return sparse_index.search(query, top_k=top_k)

def hybrid_search(
    query_embedding: list[float],
    query_text: str,
    top_k: int =5,
    rrf_k: int = 60,
    sparse_top_k: int = 20
) -> list[RetrievedChunk]:
    from app.services.sparse_vector_service import fuse_rrf
    dense_results = search(query_embedding, top_k=sparse_top_k)
    sparse_index = _build_sparse_index()
    sparse_results = sparse_index.search(query_text,top_k=sparse_top_k)
    fused = fuse_rrf([dense_results, sparse_results], rrf_k=rrf_k, top_k=top_k)
    return fused[:top_k]