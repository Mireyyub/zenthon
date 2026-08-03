"""Knowledge layer – facts, graph, retrieval."""

from knowledge.facts import FactStore
from knowledge.graph import KnowledgeGraph
from knowledge.registry import get_fact_store, get_graph, reload_all

try:
    from knowledge.retrieval import KnowledgeRetrieval
except Exception:
    KnowledgeRetrieval = None  # type: ignore

__all__ = [
    "FactStore",
    "KnowledgeGraph",
    "get_fact_store",
    "get_graph",
    "reload_all",
    "KnowledgeRetrieval",
]
