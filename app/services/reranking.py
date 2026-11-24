import logging
from typing import cast
from app.config import settings
from app.models import RetrievedChunk

logger = logging.getLogger(__name__)


class Reranker:
    def __init__(self) -> None:
        self.backend = settings.reranking_backend
        self.local_model: object | None = None
        self._voyage_client: object | None = None
    
    def _load_local_model(self) -> object:
        if self.local_model is None:
            from sentence_transformers import CrossEncoder
            self.local_model = CrossEncoder(settings.reranker_model)
        return self.local_model
    
    def _load_voyage_client(self) -> object:
        if self._voyage_client is None:
            import voyageai
            if not settings.voyage_api_key:
                raise ValueError("Voyage API key is not set.")
            self._voyage_client = voyageai.Client(api_key=settings.voyage_api_key)
        return self._voyage_client
    
    def _rerank_local(self, query: str, chunks: list[RetrievedChunk],top_k: int) -> list[RetrievedChunk]:
        local_model = self._load_local_model()
        scores = local_model.predict([(query, chunk.text) for chunk in chunks])
        scored = [RetrievedChunk(chunk.text, source = chunk.source, score=score,) for chunk, score in zip(chunks, scores,strict=True)]
        scored.sort(key=lambda c: c.score, reverse=True)
        return scored[:top_k]
    
    def _rerank_voyage(self, query: str, chunks: list[RetrievedChunk], top_k: int) -> list[RetrievedChunk]:
        client = self._load_voyage_client()
        documents = [chunk.text for chunk in chunks]
        results = client.rerank(query=query, 
                    documents=documents,
                    model= settings.reranker_model,
                    top_k=top_k)
        scored = [RetrievedChunk(chunk.text, source = chunk.source, score=score,) for chunk, score in zip(chunks, results,strict=True)]
        scored.sort(key=lambda c: c.score, reverse=True)
        return scored[:top_k]