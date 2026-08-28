"""
Durable Task model (Phase 1 contract).

Compatible with existing brain.planning.schema.PlanTask concepts.
PlanTask remains the planner's in-memory unit; Task is the future
durable unit for Task Engine (Phase 7) and API / UI surfaces.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid


class TaskStatus(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    READY = "ready"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"


class TaskPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


def new_task_id() -> str:
    return "TK-" + uuid.uuid4().hex[:10]


@dataclass
class TaskResult:
    success: bool
    output: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "TaskResult":
        return cls(
            success=bool(d.get("success", False)),
            output=d.get("output"),
            error=d.get("error"),
            metadata=dict(d.get("metadata") or {}),
        )


@dataclass
class Task:
    """Durable task record. Safe for JSON persistence and API."""

    id: str
    title: str
    goal: str = ""
    action: str = "noop"  # reason | agent | teach | retrieve | plan | custom
    params: Dict[str, Any] = field(default_factory=dict)
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.NORMAL
    depends_on: List[str] = field(default_factory=list)
    agent_name: Optional[str] = None
    plan_id: Optional[str] = None
    result: Optional[TaskResult] = None
    progress: float = 0.0  # 0.0 .. 1.0
    error: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def touch(self) -> None:
        self.updated_at = datetime.now().isoformat()

    def mark_running(self) -> None:
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.now().isoformat()
        self.touch()

    def mark_done(self, result: Optional[TaskResult] = None) -> None:
        self.status = TaskStatus.DONE
        self.progress = 1.0
        self.finished_at = datetime.now().isoformat()
        if result is not None:
            self.result = result
        self.touch()

    def mark_failed(self, error: str) -> None:
        self.status = TaskStatus.FAILED
        self.error = error[:2000]
        self.finished_at = datetime.now().isoformat()
        self.result = TaskResult(success=False, error=self.error)
        self.touch()

    def mark_cancelled(self) -> None:
        self.status = TaskStatus.CANCELLED
        self.finished_at = datetime.now().isoformat()
        self.touch()

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "id": self.id,
            "title": self.title,
            "goal": self.goal,
            "action": self.action,
            "params": self.params,
            "status": self.status.value if isinstance(self.status, TaskStatus) else self.status,
            "priority": self.priority.value if isinstance(self.priority, TaskPriority) else self.priority,
            "depends_on": list(self.depends_on),
            "agent_name": self.agent_name,
            "plan_id": self.plan_id,
            "result": self.result.to_dict() if self.result else None,
            "progress": self.progress,
            "error": self.error,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "metadata": self.metadata,
        }
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Task":
        status_raw = d.get("status") or "pending"
        priority_raw = d.get("priority") or "normal"
        try:
            status = TaskStatus(status_raw)
        except ValueError:
            status = TaskStatus.PENDING
        try:
            priority = TaskPriority(priority_raw)
        except ValueError:
            priority = TaskPriority.NORMAL

        result = None
        if d.get("result"):
            result = TaskResult.from_dict(d["result"])

        return cls(
            id=d.get("id") or new_task_id(),
            title=d.get("title") or "",
            goal=d.get("goal") or "",
            action=d.get("action") or "noop",
            params=dict(d.get("params") or {}),
            status=status,
            priority=priority,
            depends_on=list(d.get("depends_on") or []),
            agent_name=d.get("agent_name"),
            plan_id=d.get("plan_id"),
            result=result,
            progress=float(d.get("progress") or 0.0),
            error=d.get("error"),
            created_at=d.get("created_at") or datetime.now().isoformat(),
            updated_at=d.get("updated_at") or datetime.now().isoformat(),
            started_at=d.get("started_at"),
            finished_at=d.get("finished_at"),
            metadata=dict(d.get("metadata") or {}),
        )

    @classmethod
    def from_plan_task(cls, plan_task: Any, plan_id: Optional[str] = None, goal: str = "") -> "Task":
        """Bridge from brain.planning.schema.PlanTask without hard import."""
        pid = getattr(plan_task, "id", None) or new_task_id()
        status_raw = getattr(plan_task, "status", "pending") or "pending"
        try:
            status = TaskStatus(status_raw)
        except ValueError:
            status = TaskStatus.PENDING
        return cls(
            id=str(pid),
            title=getattr(plan_task, "title", "") or "",
            goal=goal,
            action=getattr(plan_task, "action", "noop") or "noop",
            params=dict(getattr(plan_task, "params", None) or {}),
            status=status,
            depends_on=list(getattr(plan_task, "depends_on", None) or []),
            plan_id=plan_id,
            error=getattr(plan_task, "error", None),
            result=(
                TaskResult(success=True, output=getattr(plan_task, "result", None))
                if getattr(plan_task, "result", None) is not None
                else None
            ),
        )
