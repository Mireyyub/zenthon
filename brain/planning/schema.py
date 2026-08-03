"""Plan schema (Faza 6 / spec 023 minimal)."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid


TASK_STATUS = ("pending", "ready", "running", "done", "failed", "skipped")
PLAN_STATUS = ("draft", "active", "completed", "failed", "cancelled")


@dataclass
class PlanTask:
    id: str
    title: str
    action: str = "noop"  # teach | reason | agent | retrieve | custom
    params: Dict[str, Any] = field(default_factory=dict)
    depends_on: List[str] = field(default_factory=list)
    status: str = "pending"
    result: Optional[Any] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "PlanTask":
        return cls(
            id=d.get("id") or "T-" + uuid.uuid4().hex[:6],
            title=d.get("title") or "",
            action=d.get("action") or "noop",
            params=d.get("params") or {},
            depends_on=list(d.get("depends_on") or []),
            status=d.get("status") or "pending",
            result=d.get("result"),
            error=d.get("error"),
        )


@dataclass
class Plan:
    id: str
    goal: str
    tasks: List[PlanTask] = field(default_factory=list)
    status: str = "draft"
    version: int = 1
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "goal": self.goal,
            "tasks": [t.to_dict() for t in self.tasks],
            "status": self.status,
            "version": self.version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Plan":
        return cls(
            id=d.get("id") or "P-" + uuid.uuid4().hex[:8],
            goal=d.get("goal") or "",
            tasks=[PlanTask.from_dict(t) for t in (d.get("tasks") or [])],
            status=d.get("status") or "draft",
            version=int(d.get("version") or 1),
            created_at=d.get("created_at") or datetime.now().isoformat(),
            updated_at=d.get("updated_at") or datetime.now().isoformat(),
            metadata=d.get("metadata") or {},
        )


def new_plan_id() -> str:
    return "P-" + uuid.uuid4().hex[:8]


def new_task_id() -> str:
    return "T-" + uuid.uuid4().hex[:6]
