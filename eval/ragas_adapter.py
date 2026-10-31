from __future__ import annotations

import os

import openai

from datasets import Dataset
from langchain_openai import OpenAIEmbeddings
from ragas import evaluate
from ragas.embedding import LangChainEmbeddingsWrapper
from ragas.llms import llm_factory
from ragas.metrics import (answer_relevancy,
                        context_precision,
                        context_recall,
                        faithfulness)

from app.config import settings

METRICS = [answer_relevancy, context_precision, context_recall, faithfulness]

def _get_llm_factory():
    """Get the LLM factory based on the current settings."""
    os.environ.setdefault("OPENAI_API_KEY", settings.openai_api_key)
    return llm_factory(settings.llm.model_grader)


def _get_ragas_embeddings():
    """Get the RAGAS embeddings based on the current settings."""
    lc_emb = OpenAIEmbeddings(
        model = settings.openai.embeddings_model,
        openai_api_key = settings.openai_api_key
    )
    return LangChainEmbeddingsWrapper(lc_emb)

def build_dataset(rows: list[dict]) -> Dataset:
    """Build a Hugging Face Dataset from a list of dictionaries."""
    
    return Dataset.from_dict(
        {
            "user_input": [r["question"] for r in rows],
            "response": [r["answer"] for r in rows],
            "retrieved_context": [r["retrieved_context"] for r in rows],
            "reference": [r["reference"] for r in rows]
        }
    )
def run(rows: list[dict]) -> list[dict]:
    """Run the evaluation on the given rows and return the results."""
    if not rows:
        return []
    dataset = build_dataset(rows)
    llm = _get_llm_factory()
    embeddings = _get_ragas_embeddings()
    return evaluate(
        dataset,
        llm=llm,
        embeddings=embeddings,
        metrics=METRICS
    )