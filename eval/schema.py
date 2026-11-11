from __future__ import annotations
from pathlib import Path
from typing import Literal

import yaml
from loguru import logger

from pydantic import BaseModel,Field,model_validator

INTENT_VALUES = ["rag", "sql", "hybrid", "web_fallback"]
FEATURE_VALUES = [
    "baseline",
    "sparse",
    "dense",
    "hybrid",
    "rerank",
    "hyde",
    "crag",
    "self_rag",
    "sql",
    "hybrid_rag_sql",
    "security",
    "wild"
]

Intent = Literal["rag", "sql", "hybrid", "web_fallback"]
Feature = Literal[
    "baseline",
    "sparse",
    "dense",
    "hybrid",
    "rerank",
    "hyde",
    "crag",
    "self_rag",
    "sql",
    "hybrid_rag_sql",
    "security",
    "wild",
]

class Golden(BaseModel):
    id: str = Field(..., pattern=r"^q-\d{3}$")
    question: str = Field(..., min_length=1)
    intent: Intent
    golden_sources: list[str] = Field(..., min_length=1)
    golden_answer_keywords: list[str] = Field(..., min_length=1)
    demonstrates_feature: Feature
    expected_baseline: Literal["pass", "fail"]
    expected_with_feature: Literal["pass"]
    notes: str
    forbidden_keywords: list[str] = Field(default_factory=list)
    
    @model_validator(mode="after")
    def check_expected_with_feature(self) -> "Golden":
        expected_with_feature = self.expected_with_feature
        if expected_with_feature != "pass":
            raise ValueError("expected_with_feature must be 'pass'")
        return self
def load_goldens(path: Path) -> list[Golden]:
    path = Path(path)
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError(f"Expected YAML root to be a list, got {type(raw).__name__}")
    goldens = [Golden(**entry) for entry in raw]
    
    ids= [golden.id for golden in goldens]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate IDs found in goldens")
    present_features = {g.demonstrates_feature for g in goldens}
    all_features = set(FEATURE_VALUES)
    missing_features = all_features - present_features
    if missing_features:
        logger.warning(
            "Seed questions do not cover all features. Missing: {}",
            sorted(missing_features),
        )
    return goldens