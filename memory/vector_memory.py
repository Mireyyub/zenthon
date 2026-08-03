"""
Vector Memory – semantik axtarış + disk (Faza 1).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
import hashlib
import math
import re

from core.logger import logger
from core.persistence import write_json, read_json


def _tokenize(text: str) -> List[str]:
    return re.findall(r"\w+", text.lower())


def _bow_embed(text: str) -> Dict[str, float]:
    tokens = _tokenize(text)
    if not tokens:
        return {}
    counts: Dict[str, int] = {}
    for t in tokens:
        counts[t] = counts.get(t, 0) + 1
    norm = math.sqrt(sum(c * c for c in counts.values())) or 1.0
    return {t: c / norm for t, c in counts.items()}


def _cosine_bow(a: Dict[str, float], b: Dict[str, float]) -> float:
    if not a or not b:
        return 0.0
    common = set(a) & set(b)
    return sum(a[t] * b[t] for t in common)


def _cosine_dense(a: List[float], b: List[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(y * y for y in b)) or 1.0
    return dot / (na * nb)


class VectorMemory:
    def __init__(
        self,
        use_llm_embeddings: bool = True,
        path: Optional[Path | str] = None,
        auto_persist: bool = True,
    ):
        if path is None:
            try:
                from core.config import config

                path = config.path.memory_dir / "vector.json"
            except Exception:
                path = Path("data/leon/memory/vector.json")
        self.path = Path(path)
        self.auto_persist = auto_persist
        self._docs: Dict[str, Dict[str, Any]] = {}
        self.use_llm_embeddings = use_llm_embeddings
        self._llm_ok: Optional[bool] = None
        self.load()

    def _try_dense(self, text: str) -> Optional[List[float]]:
        if not self.use_llm_embeddings:
            return None
        if self._llm_ok is False:
            return None
        try:
            from brain.llm.client import get_llm_client

            client = get_llm_client()
            vec = client.embed(text)
            if vec and isinstance(vec, list) and len(vec) > 8:
                self._llm_ok = True
                return vec
            self._llm_ok = False
            return None
        except Exception as e:
            logger.debug(f"Dense embed unavailable: {e}")
            self._llm_ok = False
            return None

    def add(self, text: str, metadata: Optional[Dict] = None) -> str:
        doc_id = hashlib.md5(text.encode()).hexdigest()[:12]
        dense = self._try_dense(text)
        self._docs[doc_id] = {
            "id": doc_id,
            "text": text,
            "embedding_bow": _bow_embed(text),
            "embedding_dense": dense,
            "metadata": metadata or {},
            "created_at": datetime.now().isoformat(),
        }
        if self.auto_persist:
            self.save()
        return doc_id

    def search(self, query: str, top_k: int = 5) -> List[Tuple[str, float]]:
        q_dense = self._try_dense(query)
        q_bow = _bow_embed(query)
        scored = []

        for doc in self._docs.values():
            score = 0.0
            if q_dense and doc.get("embedding_dense"):
                score = _cosine_dense(q_dense, doc["embedding_dense"])
            else:
                score = _cosine_bow(q_bow, doc.get("embedding_bow") or {})
            if score > 0.05:
                scored.append((doc["text"], float(score), doc["id"]))

        scored.sort(key=lambda x: x[1], reverse=True)
        return [(text, score) for text, score, _ in scored[:top_k]]

    def get(self, doc_id: str) -> Optional[Dict]:
        return self._docs.get(doc_id)

    def count(self) -> int:
        return len(self._docs)

    def clear(self) -> None:
        self._docs.clear()
        if self.auto_persist:
            self.save()

    def backend(self) -> str:
        if self._llm_ok is True:
            return "dense_llm"
        if self._llm_ok is False:
            return "bag_of_words"
        return "auto"

    def save(self) -> None:
        # dense vectors can be large; still persist for restart
        write_json(self.path, {"docs": self._docs})

    def load(self) -> int:
        data = read_json(self.path, default={})
        if isinstance(data, dict) and "docs" in data:
            self._docs = data["docs"] or {}
        return len(self._docs)
