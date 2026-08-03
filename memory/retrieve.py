"""
Vahid retrieval pipeline (spec 011 / GraphRAG hybrid) – Faza 4.

query → candidates (facts + graph + vector + semantic) → rank → validate
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import re


@dataclass
class Candidate:
    content: str
    source: str  # fact | graph | vector | semantic | working
    score: float
    ref: str = ""
    verified: bool = True
    meta: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content[:500],
            "source": self.source,
            "score": round(self.score, 4),
            "ref": self.ref,
            "verified": self.verified,
            "meta": self.meta,
        }


def _tokenize(q: str) -> List[str]:
    return [t for t in re.findall(r"\w+", (q or "").lower()) if len(t) > 1]


def _overlap_score(query: str, text: str) -> float:
    qt = set(_tokenize(query))
    tt = set(_tokenize(text))
    if not qt or not tt:
        return 0.0
    inter = len(qt & tt)
    return inter / max(len(qt), 1)


class UnifiedRetriever:
    """FactStore + KnowledgeGraph + Vector + Semantic."""

    def __init__(self):
        self._facts = None
        self._graph = None
        self._vector = None
        self._semantic = None
        self._working = None

    def _backends(self):
        if self._facts is None:
            try:
                from knowledge.facts import FactStore

                self._facts = FactStore()
            except Exception:
                self._facts = False
        if self._graph is None:
            try:
                from knowledge.graph import KnowledgeGraph

                self._graph = KnowledgeGraph()
            except Exception:
                self._graph = False
        if self._vector is None:
            try:
                from memory.vector_memory import VectorMemory

                self._vector = VectorMemory()
            except Exception:
                self._vector = False
        if self._semantic is None:
            try:
                from memory.semantic import SemanticMemory

                self._semantic = SemanticMemory()
            except Exception:
                self._semantic = False

    def retrieve(
        self,
        query: str,
        top_k: int = 8,
        min_score: float = 0.08,
        include_unverified: bool = False,
    ) -> Dict[str, Any]:
        self._backends()
        candidates: List[Candidate] = []

        # Facts
        if self._facts:
            try:
                for f in self._facts.search(query, top_k=top_k):
                    stmt = f.get("statement", "")
                    score = max(_overlap_score(query, stmt), 0.15 * float(f.get("confidence", 1)))
                    candidates.append(
                        Candidate(
                            content=stmt,
                            source="fact",
                            score=score + 0.2,
                            ref=f.get("id", ""),
                            verified=True,
                            meta={"confidence": f.get("confidence"), "src": f.get("source")},
                        )
                    )
            except Exception:
                pass

        # Graph nodes + neighbors
        if self._graph:
            try:
                for n in self._graph.query(query, top_k=top_k):
                    label = n.get("label", "")
                    score = _overlap_score(query, label) + 0.25
                    candidates.append(
                        Candidate(
                            content=label,
                            source="graph",
                            score=score,
                            ref=n.get("id", ""),
                            verified=True,
                            meta={"type": n.get("type")},
                        )
                    )
                    for neigh, rel in self._graph.neighbors(n["id"])[:3]:
                        candidates.append(
                            Candidate(
                                content=f"{label} -{rel}-> {neigh.get('label')}",
                                source="graph",
                                score=score * 0.85,
                                ref=neigh.get("id", ""),
                                verified=True,
                                meta={"relation": rel},
                            )
                        )
            except Exception:
                pass

        # Vector
        if self._vector:
            try:
                for text, sc in self._vector.search(query, top_k=top_k):
                    candidates.append(
                        Candidate(
                            content=text,
                            source="vector",
                            score=float(sc),
                            ref="vector",
                            verified=True,
                        )
                    )
            except Exception:
                pass

        # Semantic triples
        if self._semantic:
            try:
                tok = _tokenize(query)
                subj = tok[0] if tok else None
                for fact in self._semantic.query(subject=subj)[:top_k]:
                    text = f"{fact['subject']} {fact['predicate']} {fact['object']}"
                    candidates.append(
                        Candidate(
                            content=text,
                            source="semantic",
                            score=_overlap_score(query, text) + 0.15,
                            ref=fact.get("id", ""),
                            verified=True,
                            meta={"confidence": fact.get("confidence")},
                        )
                    )
            except Exception:
                pass

        # Rank
        ranked = sorted(candidates, key=lambda c: c.score, reverse=True)

        # Validate: drop weak / optional unverified
        validated = []
        for c in ranked:
            if c.score < min_score:
                continue
            if not c.verified and not include_unverified:
                continue
            # de-dup by content prefix
            key = c.content[:120].lower()
            if any(v.content[:120].lower() == key for v in validated):
                continue
            validated.append(c)
            if len(validated) >= top_k:
                break

        return {
            "query": query,
            "candidates": [c.to_dict() for c in validated],
            "total_raw": len(candidates),
            "returned": len(validated),
        }


def retrieve(query: str, top_k: int = 8, **kw) -> Dict[str, Any]:
    return UnifiedRetriever().retrieve(query, top_k=top_k, **kw)
