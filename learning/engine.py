"""
Learning Engine (spec 022).

Observe -> Normalize -> Parse -> Compare -> Validate -> Learn -> Index
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import hashlib
import uuid

from core.logger import logger
from core.event_bus import event_bus


@dataclass
class LearningRecord:
    id: str
    source: str
    content: str
    confidence: float
    status: str = "pending"  # pending | validated | rejected
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


class LearningEngine:
    """Validated observations → durable knowledge (spec 022)."""

    CONFIDENCE_VALIDATE = 0.75
    CONFIDENCE_REJECT = 0.25

    def __init__(self):
        self._records: Dict[str, LearningRecord] = {}
        self._quarantine: List[LearningRecord] = []
        self._facts = None
        self._memory = None
        self._graph = None

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
        """Pipeline entry: normalize + parse + compare + validate."""
        self._backends()
        normalized = self._normalize(content)
        rid = "LR-" + hashlib.md5(normalized.encode()).hexdigest()[:10]

        # Compare against existing
        conflict = self._find_conflict(normalized)

        status = "pending"
        if conflict:
            status = "pending"  # pending_review semantics
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
            # naive negation conflict
            if rec.content.lower() in low or low in rec.content.lower():
                continue
            if ("xeyr" in low and "bəli" in rec.content.lower()) or (
                "bəli" in low and "xeyr" in rec.content.lower()
            ):
                if any(t in low and t in rec.content.lower() for t in low.split() if len(t) > 3):
                    return rec.id
        return None

    def _commit(self, rec: LearningRecord) -> None:
        """Memory promotion: → semantic / facts / graph."""
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
        return rec

    def from_curriculum(self, volume_id: str = "01") -> Dict[str, Any]:
        """Curriculum train.jsonl → learning records."""
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
        }


learning_engine = LearningEngine()
