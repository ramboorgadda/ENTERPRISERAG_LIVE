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
