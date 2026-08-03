"""
Learning Engine (spec 022) + disk persistence (Faza 1).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path
import hashlib

from core.logger import logger
from core.event_bus import event_bus
from core.persistence import write_json, read_json


@dataclass
class LearningRecord:
    id: str
    source: str
    content: str
    confidence: float
    status: str = "pending"
    provenance: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "source": self.source,
            "content": self.content,
            "confidence": self.confidence,
            "status": self.status,
            "provenance": self.provenance,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "LearningRecord":
        return cls(
            id=d.get("id", ""),
            source=d.get("source", ""),
            content=d.get("content", ""),
            confidence=float(d.get("confidence", 0.5)),
            status=d.get("status", "pending"),
            provenance=d.get("provenance") or {},
            created_at=d.get("created_at") or datetime.now().isoformat(),
        )


class LearningEngine:
    CONFIDENCE_VALIDATE = 0.75
    CONFIDENCE_REJECT = 0.25

    def __init__(self, path: Optional[Path | str] = None, auto_persist: bool = True):
        if path is None:
            try:
                from core.config import config

                path = config.path.learning_dir / "records.json"
            except Exception:
                path = Path("data/leon/learning/records.json")
        self.path = Path(path)
        self.auto_persist = auto_persist
        self._records: Dict[str, LearningRecord] = {}
        self._quarantine: List[LearningRecord] = []
        self._facts = None
        self._memory = None
        self._graph = None
        self.load()

    def _backends(self):
        if self._facts is None:
            try:
                from knowledge.facts import FactStore

                self._facts = FactStore()
            except Exception:
                self._facts = None
        if self._memory is None:
            try:
                from memory import MemoryManager

                self._memory = MemoryManager()
            except Exception:
                self._memory = None
        if self._graph is None:
            try:
                from knowledge.graph import KnowledgeGraph

                self._graph = KnowledgeGraph()
            except Exception:
                self._graph = None

    def observe(
        self,
        content: str,
        source: str = "user",
        confidence: float = 0.5,
        metadata: Optional[Dict] = None,
    ) -> LearningRecord:
        self._backends()
        normalized = self._normalize(content)
        rid = "LR-" + hashlib.md5(normalized.encode()).hexdigest()[:10]

        conflict = self._find_conflict(normalized)

        status = "pending"
        if conflict:
            status = "pending"
            confidence = min(confidence, 0.5)
        elif confidence >= self.CONFIDENCE_VALIDATE:
            status = "validated"
        elif confidence <= self.CONFIDENCE_REJECT:
            status = "rejected"

        rec = LearningRecord(
            id=rid,
            source=source,
            content=normalized,
            confidence=max(0.0, min(1.0, float(confidence))),
            status=status,
            provenance={"metadata": metadata or {}, "conflict": conflict},
        )

        if status == "rejected":
            self._quarantine.append(rec)
        else:
            self._records[rid] = rec

        if status == "validated":
            self._commit(rec)

        if self.auto_persist:
            self.save()

        event_bus.publish(
            "LearningObserved",
            {"id": rid, "status": status, "confidence": rec.confidence},
            source="learning_engine",
        )
        logger.info(f"LearningEngine: {rid} status={status} conf={rec.confidence:.2f}")
        return rec

    def learn(self, content: str, source: str = "system", confidence: float = 0.8, **kw) -> Dict[str, Any]:
        rec = self.observe(content, source=source, confidence=confidence, metadata=kw or None)
        return {
            "record": rec.to_dict(),
            "knowledge_update": rec.status == "validated",
            "confidence": rec.confidence,
            "trace": {
                "pipeline": "observe→normalize→compare→validate→learn→index",
                "status": rec.status,
            },
        }

    def _normalize(self, content: str) -> str:
        return " ".join((content or "").strip().split())

    def _find_conflict(self, content: str) -> Optional[str]:
        low = content.lower()
        for rec in self._records.values():
            if rec.status != "validated":
                continue
            if rec.content.lower() in low or low in rec.content.lower():
                continue
            if ("xeyr" in low and "bəli" in rec.content.lower()) or (
                "bəli" in low and "xeyr" in rec.content.lower()
            ):
                if any(t in low and t in rec.content.lower() for t in low.split() if len(t) > 3):
                    return rec.id
        return None

    def _commit(self, rec: LearningRecord) -> None:
        if self._facts:
            try:
                self._facts.add(rec.content, source=f"learning:{rec.source}")
            except Exception:
                pass
        if self._memory:
            try:
                self._memory.remember(
                    rec.content,
                    kind="vector",
                    metadata={"learning_id": rec.id, "confidence": rec.confidence},
                )
            except Exception:
                pass
        event_bus.publish("KnowledgeUpdated", {"id": rec.id}, source="learning_engine")

    def validate_record(self, record_id: str, accept: bool = True) -> Optional[LearningRecord]:
        rec = self._records.get(record_id)
        if not rec:
            return None
        rec.status = "validated" if accept else "rejected"
        if accept:
            self._commit(rec)
        else:
            self._quarantine.append(rec)
        if self.auto_persist:
            self.save()
        return rec

    def from_curriculum(self, volume_id: str = "01") -> Dict[str, Any]:
        from curriculum.volume import load_train_jsonl

        rows = load_train_jsonl(volume_id)
        results = []
        for row in rows:
            text = f"Q: {row.get('instruction')} → A: {row.get('output')}"
            results.append(
                self.learn(text, source=f"curriculum:{volume_id}", confidence=0.9, id=row.get("id")).get(
                    "record"
                )
            )
        return {"learned": len(results), "records": results}

    def stats(self) -> Dict[str, Any]:
        by_status: Dict[str, int] = {}
        for r in self._records.values():
            by_status[r.status] = by_status.get(r.status, 0) + 1
        return {
            "records": len(self._records),
            "quarantine": len(self._quarantine),
            "by_status": by_status,
            "path": str(self.path),
        }

    def save(self) -> None:
        write_json(
            self.path,
            {
                "records": {k: v.to_dict() for k, v in self._records.items()},
                "quarantine": [r.to_dict() for r in self._quarantine],
            },
        )

    def load(self) -> int:
        data = read_json(self.path, default={})
        if not isinstance(data, dict):
            return 0
        self._records = {
            k: LearningRecord.from_dict(v) for k, v in (data.get("records") or {}).items()
        }
        self._quarantine = [LearningRecord.from_dict(r) for r in (data.get("quarantine") or [])]
        return len(self._records)


learning_engine = LearningEngine()
