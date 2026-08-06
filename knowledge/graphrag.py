"""GraphRAG hybrid – registry-backed."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.logger import logger


class GraphRAG:
    def __init__(self):
        self._vector = None
        self._graph = None
        self._facts = None

    def _ensure(self):
        if self._vector is None:
            try:
                from memory.vector_memory import VectorMemory

                self._vector = VectorMemory()
            except Exception:
                self._vector = None
        if self._graph is None:
            try:
                from knowledge.registry import get_graph

                self._graph = get_graph()
            except Exception:
                self._graph = None
        if self._facts is None:
            try:
                from knowledge.registry import get_fact_store

                self._facts = get_fact_store()
            except Exception:
                self._facts = None

    def ingest(self, text: str, entities: Optional[List[str]] = None) -> None:
        self._ensure()
        if self._vector:
            self._vector.add(text)
        if self._facts:
            self._facts.add(text, source="graphrag")
        if self._graph and entities:
            ids = []
            for ent in entities:
                found = self._graph.find_by_label(ent)
                if found:
                    ids.append(found[0]["id"])
                else:
                    ids.append(self._graph.add_node(ent, node_type="entity"))
            for i in range(len(ids) - 1):
                try:
                    self._graph.add_edge(ids[i], ids[i + 1], "co_occurs")
                except Exception:
                    pass

    def retrieve(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        self._ensure()
        result: Dict[str, Any] = {
            "query": query,
            "vector": [],
            "facts": [],
            "nodes": [],
            "graph_context": [],
            "combined": [],
            "unified": [],
        }

        # Prefer UnifiedRetriever when available
        try:
            from memory.retrieve import retrieve as unified

            ur = unified(query, top_k=top_k)
            result["unified"] = ur.get("candidates") or []
            result["combined"] = [c.get("content", "") for c in result["unified"]]
            if result["combined"]:
                return result
        except Exception:
            pass

        if self._vector:
            hits = self._vector.search(query, top_k=top_k)
            result["vector"] = [{"text": t, "score": s} for t, s in hits]

        if self._facts:
            result["facts"] = self._facts.search(query, top_k=top_k)

        if self._graph:
            tokens = (query or "").split()
            seed = tokens[0] if tokens else ""
            nodes = self._graph.find_by_label(seed) if seed else []
            if not nodes:
                nodes = self._graph.query(query, top_k=top_k)
            result["nodes"] = nodes
            for n in nodes[:5]:
                for nb, rel in self._graph.neighbors(n["id"])[:5]:
                    result["graph_context"].append(
                        f"{n['label']} --{rel}--> {nb.get('label')}"
                    )

        combined: List[str] = []
        for v in result["vector"]:
            combined.append(v["text"])
        for f in result["facts"]:
            if isinstance(f, dict):
                combined.append(f.get("statement", str(f)))
            else:
                combined.append(str(f))
        combined.extend(result["graph_context"])

        seen = set()
        unique = []
        for c in combined:
            k = c[:100]
            if k not in seen:
                seen.add(k)
                unique.append(c)
        result["combined"] = unique[: top_k + 3]
        logger.debug(f"GraphRAG retrieve: {len(result['combined'])} snippets")
        return result

    def as_context_block(self, query: str, top_k: int = 5) -> str:
        data = self.retrieve(query, top_k=top_k)
        if not data["combined"]:
            return ""
        lines = ["[GraphRAG Context]"]
        for i, snip in enumerate(data["combined"], 1):
            lines.append(f"{i}. {snip[:250]}")
        return "\n".join(lines)
