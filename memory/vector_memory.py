"""
Vector Memory – semantik axtarış (RAG üçün hazırlıq).

Sadə bag-of-words embedding (external model yoxdur).
Gələcəkdə Ollama / sentence-transformers ilə əvəz oluna bilər.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
import hashlib
import math
import re


def _tokenize(text: str) -> List[str]:
    return re.findall(r"\w+", text.lower())


def _embed(text: str) -> Dict[str, float]:
    """Sadə TF vektoru."""
    tokens = _tokenize(text)
    if not tokens:
        return {}
    counts: Dict[str, int] = {}
    for t in tokens:
        counts[t] = counts.get(t, 0) + 1
    norm = math.sqrt(sum(c * c for c in counts.values())) or 1.0
    return {t: c / norm for t, c in counts.items()}


def _cosine(a: Dict[str, float], b: Dict[str, float]) -> float:
    if not a or not b:
        return 0.0
    common = set(a) & set(b)
    return sum(a[t] * b[t] for t in common)


class VectorMemory:
    def __init__(self):
        self._docs: Dict[str, Dict[str, Any]] = {}

    def add(self, text: str, metadata: Optional[Dict] = None) -> str:
        doc_id = hashlib.md5(text.encode()).hexdigest()[:12]
        self._docs[doc_id] = {
            "id": doc_id,
            "text": text,
            "embedding": _embed(text),
            "metadata": metadata or {},
            "created_at": datetime.now().isoformat(),
        }
        return doc_id

    def search(self, query: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """(text, score) siyahısı qaytarır."""
        q_emb = _embed(query)
        scored = []
        for doc in self._docs.values():
            score = _cosine(q_emb, doc["embedding"])
            if score > 0:
                scored.append((doc["text"], score, doc["id"]))
        scored.sort(key=lambda x: x[1], reverse=True)
        return [(text, score) for text, score, _ in scored[:top_k]]

    def get(self, doc_id: str) -> Optional[Dict]:
        return self._docs.get(doc_id)

    def count(self) -> int:
        return len(self._docs)

    def clear(self) -> None:
        self._docs.clear()
