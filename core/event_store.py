"""Bounded, privacy-aware read model for desktop operational events.

The in-process event bus remains the source of immediate notifications.  This
module deliberately stores only a small, allowlisted operational projection for
the GUI and loopback API; it never persists prompts, answers, raw reasoning, or
arbitrary nested payloads.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import threading
from typing import Any, Dict, Iterable, List, Optional, TYPE_CHECKING

from core.logger import logger
from core.persistence import read_json, write_json

if TYPE_CHECKING:
    from core.event_bus import Event


_PUBLIC_PAYLOAD_KEYS = frozenset(
    {
        "agent",
        "agent_id",
        "confidence",
        "confidence_label",
        "count",
        "cycle",
        "id",
        "kind",
        "llm_used",
        "mode",
        "model",
        "name",
        "operation",
        "reasoning_mode",
        "source",
        "status",
        "success",
        "task_id",
        "tasks",
        "trace_id",
        "type",
    }
)
_SENSITIVE_KEYS = frozenset(
    {
        "answer",
        "arg",
        "chain_of_thought",
        "content",
        "context",
        "error",
        "evidence",
        "goal",
        "output",
        "prompt",
        "query",
        "raw_reasoning",
        "reasoning",
        "result",
        "task",
        "text",
    }
)


def _event_severity(name: str, payload: Dict[str, Any]) -> str:
    """Classify operational state without interpreting private content."""
    normalized = name.lower()
    if payload.get("success") is False or any(token in normalized for token in ("fail", "error", "denied")):
        return "error"
    if any(token in normalized for token in ("warning", "paused", "fallback", "unknown")):
        return "warning"
    return "info"


def _safe_scalar(value: Any) -> Optional[Any]:
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return round(value, 6)
    if isinstance(value, str):
        return value[:160]
    return None


def _project_payload(payload: Dict[str, Any]) -> tuple[Dict[str, Any], int]:
    """Return an allowlisted payload projection and a redaction counter."""
    public: Dict[str, Any] = {}
    redacted = 0
    for key, value in (payload or {}).items():
        if key in _SENSITIVE_KEYS or key not in _PUBLIC_PAYLOAD_KEYS:
            redacted += 1
            continue
        safe_value = _safe_scalar(value)
        if safe_value is None:
            redacted += 1
            continue
        public[key] = safe_value
    return public, redacted


def _timestamp(value: Any) -> str:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class EventRecord:
    """A compact, non-sensitive event representation exposed to local clients."""

    event_id: str
    name: str
    source: str
    timestamp: str
    severity: str
    summary: str
    data: Dict[str, Any]
    redacted_field_count: int = 0

    @classmethod
    def from_event(cls, event: "Event") -> "EventRecord":
        payload, redacted = _project_payload(event.payload)
        return cls(
            event_id=event.event_id,
            name=event.name,
            source=event.source,
            timestamp=_timestamp(event.timestamp),
            severity=_event_severity(event.name, payload),
            summary=f"{event.source}: {event.name}",
            data=payload,
            redacted_field_count=redacted,
        )

    @classmethod
    def from_dict(cls, row: Dict[str, Any]) -> Optional["EventRecord"]:
        try:
            data, additional_redactions = _project_payload(dict(row.get("data") or {}))
            return cls(
                event_id=str(row["event_id"]),
                name=str(row["name"]),
                source=str(row.get("source") or "system"),
                timestamp=str(row["timestamp"]),
                severity=str(row.get("severity") or "info"),
                summary=str(row.get("summary") or "system event"),
                data=data,
                redacted_field_count=int(row.get("redacted_field_count") or 0) + additional_redactions,
            )
        except (KeyError, TypeError, ValueError):
            return None

    def as_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "name": self.name,
            "source": self.source,
            "timestamp": self.timestamp,
            "severity": self.severity,
            "summary": self.summary,
            "data": self.data,
            "redacted_field_count": self.redacted_field_count,
        }


class EventReadModel:
    """Atomic, bounded local event feed with cursor-based reads."""

    def __init__(self, path: Path | str, max_records: int = 500, persist: bool = True):
        self.path = Path(path)
        self.max_records = max(10, min(int(max_records), 5000))
        self.persist = bool(persist)
        self._lock = threading.RLock()
        self._records: List[EventRecord] = self._load() if self.persist else []

    @classmethod
    def from_config(cls) -> "EventReadModel":
        from core.config import config

        return cls(
            config.path.leon_dir / "events" / "events.json",
            max_records=config.events.max_records,
            persist=config.events.persist,
        )

    def _load(self) -> List[EventRecord]:
        raw_rows = read_json(self.path, default=[])
        if not isinstance(raw_rows, list):
            return []
        records = [record for row in raw_rows if isinstance(row, dict) if (record := EventRecord.from_dict(row))]
        return records[-self.max_records :]

    def _save_locked(self) -> None:
        if self.persist:
            write_json(self.path, [record.as_dict() for record in self._records])

    def record(self, event: "Event") -> EventRecord:
        record = EventRecord.from_event(event)
        with self._lock:
            self._records.append(record)
            self._records = self._records[-self.max_records :]
            self._save_locked()
        return record

    def feed(self, limit: int = 50, after_event_id: Optional[str] = None) -> Dict[str, Any]:
        bounded_limit = max(1, min(int(limit), 200))
        with self._lock:
            records: Iterable[EventRecord] = self._records
            if after_event_id:
                for index, record in enumerate(self._records):
                    if record.event_id == after_event_id:
                        records = self._records[index + 1 :]
                        break
            selected = list(records)[-bounded_limit:]
            events = [record.as_dict() for record in selected]
        return {
            "events": events,
            "count": len(events),
            "cursor": events[-1]["event_id"] if events else after_event_id,
            "max_records": self.max_records,
        }

    def clear(self) -> None:
        with self._lock:
            self._records.clear()
            self._save_locked()
