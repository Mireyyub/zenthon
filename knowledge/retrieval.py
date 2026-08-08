"""Knowledge Retrieval – registry-backed GraphRAG hybrid."""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class KnowledgeRetrieval:
    def __init__(self, graph=None, facts=None):
        if graph is None or facts is None:
            from knowledge.registry import get_fact_store, get_graph

            self.graph = graph or get_graph()
            self.facts = facts or get_fact_store()
        else:
            self.graph = graph
            self.facts = facts

    def retrieve(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        base: Dict[str, Any] = {
            "facts": self.facts.search(query, top_k=top_k),
            "nodes": self.graph.find_by_label(query),
            "query": query,
        }
        try:
            from memory.retrieve import retrieve as unified

            u = unified(query, top_k=top_k)
            base["unified"] = u.get("candidates") or []
            base["returned"] = u.get("returned")
        except Exception:
            base["unified"] = []
        return base

    def add_knowledge(self, statement: str, entities: Optional[List[str]] = None) -> None:
        self.facts.add(statement)
        if entities:
            ids = []
            for ent in entities:
                found = self.graph.find_by_label(ent)
                if found:
                    ids.append(found[0]["id"])
                else:
                    ids.append(self.graph.add_node(ent))
            for i in range(len(ids) - 1):
                try:
                    self.graph.add_edge(ids[i], ids[i + 1], "related_to")
                except Exception:
                    pass
