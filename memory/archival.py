"""
Archival Memory – uzunmüddətli arxiv qatı (MemGPT-inspired tier).

Working / session qısa qalır; vacib bilik buraya köçürülür.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from datetime import datetime
import hashlib
import json
from pathlib import Path

from core.logger import logger


class ArchivalMemory:
    def __init__(self, path: str = ".zenthon_archival.json"):
        self.path = Path(path)
        self._store: Dict[str, Dict[str, Any]] = {}
        self._load()

    def _load(self) -> None:
        if self.path.exists():
            try:
                self._store = json.loads(self.path.read_text(encoding="utf-8"))
            except Exception:
                self._store = {}

    def _save(self) -> None:
        try:
            self.path.write_text(
                json.dumps(self._store, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception as e:
            logger.warning(f"Archival save failed: {e}")

    def store(self, text: str, tags: Optional[List[str]] = None, importance: float = 0.5) -> str:
        key = hashlib.md5(text.encode()).hexdigest()[:12]
        self._store[key] = {
            "text": text,
            "tags": tags or [],
            "importance": importance,
            "created_at": datetime.now().isoformat(),
            "access_count": 0,
        }
        self._save()
        return key

    def search(self, query: str, top_k: int = 5) -> List[str]:
        q = query.lower().split()
        scored = []
        for item in self._store.values():
            text = item["text"].lower()
            score = sum(1 for w in q if w in text) + item.get("importance", 0) * 0.5
            if score > 0:
                scored.append((score, item))
        scored.sort(key=lambda x: x[0], reverse=True)
        results = []
        for _, item in scored[:top_k]:
            item["access_count"] = item.get("access_count", 0) + 1
            results.append(item["text"])
        self._save()
        return results

    def count(self) -> int:
        return len(self._store)
