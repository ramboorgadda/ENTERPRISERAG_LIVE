from unittest.mock import Mock

from app.models import RetrievedChunk
from app.services.reranking import Reranker


def test_local_rerank_returns_scored_chunks_in_ranked_order():
    chunks = [
        RetrievedChunk(text="first", source="first.txt", score=0.9),
        RetrievedChunk(text="second", source="second.txt", score=0.1),
        RetrievedChunk(text="third", source="third.txt", score=0.5),
    ]
    model = Mock()
    model.predict.return_value = [0.2, 0.8, 0.5]
    reranker = Reranker()
    reranker.backend = "local"
    reranker.local_model = model

    result = reranker.rerank("question", chunks, top_k=2)

    assert [(chunk.text, chunk.source, chunk.score) for chunk in result] == [
        ("second", "second.txt", 0.8),
        ("third", "third.txt", 0.5),
    ]
    model.predict.assert_called_once_with(
        [("question", "first"), ("question", "second"), ("question", "third")]
    )
