from openai import OpenAI

from app.config import settings
from app.services.query_cache_service import query_cache

openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)

def embed_texts(texts: list[str],model: str | None = None) -> list[list[float]]:
    if not texts:
        return []
    if model is None:
        model = settings.llm_model_embedding
    results: list[list[float] | None] = [None] * len(texts)
    miss_indices: list[int] = []
    miss_texts: list[str] = []
    for i, text in enumerate(texts):
        cached_embedding = query_cache.get_embedding(text)
        if cached_embedding is not None:
            results[i] = cached_embedding
        else:
            miss_indices.append(i)
            miss_texts.append(text)
    if miss_texts:
        response = openai_client.embeddings.create(model=model,input=miss_texts)
        for idx_in_misses, item in enumerate(response.data):
            original_idx = miss_indices[idx_in_misses]
            vector = item.embedding
            results[original_idx] = vector
            query_cache.set_embedding(miss_texts[idx_in_misses], vector)
    return [r for r in results if r is not None]
