from __future__ import annotations

from typing import Any
import datetime
import decimal
import json
import uuid

import psycopg
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt
from app.config import settings
from app.core.state import GraphState




class _PlaceholderGraph:
    def invoke(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        return {
            "final_answer": "Graph is not configured yet. Please complete the app graph implementation.",
            "sources": [],
            "confidence": 0.0,
            "cache_hit": False,
            "metadata": {"status": "placeholder"},
        }


def build_graph() -> _PlaceholderGraph:
    return _PlaceholderGraph()


graph = build_graph()