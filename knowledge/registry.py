"""Shared singletons – one FactStore / KnowledgeGraph per process (perfect-code + cortex)."""

from __future__ import annotations

from typing import Optional

_fact_store = None
_graph = None


def get_fact_store(force_new: bool = False):
    global _fact_store
    from knowledge.facts import FactStore

    if force_new or _fact_store is None:
        _fact_store = FactStore()
    return _fact_store


def get_graph(force_new: bool = False):
    global _graph
    from knowledge.graph import KnowledgeGraph

    if force_new or _graph is None:
        _graph = KnowledgeGraph()
    return _graph


def reload_all() -> dict:
    """Diskdən yenidən yüklə."""
    fs = get_fact_store(force_new=True)
    kg = get_graph(force_new=True)
    return {"facts": len(fs.all()), "graph": kg.stats()}
