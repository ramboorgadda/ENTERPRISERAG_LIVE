from __future__ import annotations

import os
import re
import importlib
from collections.abc import Iterable
from typing import Any

from app.config import settings

METRIC_NAMES = [
    "answer_relevancy",
    "context_precision",
    "context_recall",
    "faithfulness",
]

def _get_llm_factory():
    """Get the LLM factory based on the current settings."""
    from ragas.llms import llm_factory

    os.environ.setdefault("OPENAI_API_KEY", settings.openai_api_key)
    return llm_factory(settings.llm_model_grader)


def _get_ragas_embeddings():
    """Get the RAGAS embeddings based on the current settings."""
    from langchain_openai import OpenAIEmbeddings

    lc_emb = OpenAIEmbeddings(
        model=settings.llm_model_embedding,
        openai_api_key = settings.openai_api_key
    )
    try:
        wrapper_mod = importlib.import_module("ragas.embedding")
        wrapper_cls = getattr(wrapper_mod, "LangChainEmbeddingsWrapper")
    except Exception:
        wrapper_mod = importlib.import_module("ragas.embeddings")
        wrapper_cls = getattr(wrapper_mod, "LangchainEmbeddingsWrapper")
    return wrapper_cls(lc_emb)

def build_dataset(rows: list[dict]) -> Any:
    """Build a Hugging Face Dataset from a list of dictionaries."""

    from datasets import Dataset

    return Dataset.from_dict(
        {
            "user_input": [r["question"] for r in rows],
            "response": [r["answer"] for r in rows],
            "retrieved_contexts": [r["contexts"] for r in rows],
            "reference": [r["ground_truth"] for r in rows],
        }
    )


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-zA-Z0-9_]+", text.lower()))


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _fallback_metrics(rows: list[dict]) -> list[dict]:
    metrics: list[dict] = []
    for row in rows:
        q = _tokenize(row.get("question", ""))
        a = _tokenize(row.get("answer", ""))
        refs = _tokenize(row.get("ground_truth", ""))
        ctx_text = " ".join(row.get("contexts", []))
        c = _tokenize(ctx_text)

        metrics.append(
            {
                "answer_relevancy": _jaccard(q, a),
                "context_precision": _jaccard(a, c),
                "context_recall": _jaccard(refs, a),
                "faithfulness": _jaccard(a, c),
                "ragas_fallback": True,
            }
        )
    return metrics


def _normalize_result(result: Any, expected_len: int) -> list[dict]:
    if result is None:
        return []

    # Ragas 0.3 returns an EvaluationResult with to_pandas()
    to_pandas = getattr(result, "to_pandas", None)
    if callable(to_pandas):
        frame = to_pandas()
        records = frame.to_dict(orient="records")
        return [{k: row.get(k) for k in METRIC_NAMES} for row in records]

    if isinstance(result, Iterable):
        normalized: list[dict] = []
        for item in result:
            if isinstance(item, dict):
                normalized.append({k: item.get(k) for k in METRIC_NAMES})
        if normalized:
            return normalized

    return [{} for _ in range(expected_len)]


def run(rows: list[dict]) -> list[dict]:
    """Run the evaluation on the given rows and return the results."""
    if not rows:
        return []

    try:
        from ragas import evaluate
        from ragas.metrics import (
            answer_relevancy,
            context_precision,
            context_recall,
            faithfulness,
        )

        dataset = build_dataset(rows)
        llm = _get_llm_factory()
        embeddings = _get_ragas_embeddings()
        result = evaluate(
            dataset,
            llm=llm,
            embeddings=embeddings,
            metrics=[answer_relevancy, context_precision, context_recall, faithfulness],
        )
        return _normalize_result(result, len(rows))
    except Exception:
        # Fall back to lightweight lexical metrics if ragas/langchain stack is incompatible.
        return _fallback_metrics(rows)