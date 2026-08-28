"""
Typed event names and payload helpers.

Does NOT replace core.event_bus.Event or AsyncEventBus.
Provides a shared vocabulary so API / WebSocket / Tauri layers
speak the same event names without string drift.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
import uuid


class EventName(str, Enum):
    """Canonical event vocabulary (string values stay stable)."""

    # System / lifecycle
    SYSTEM_STARTED = "system.started"
    SYSTEM_STOPPED = "system.stopped"
    SYSTEM_HEALTH = "system.health"
    SYSTEM_ERROR = "system.error"

    # User / chat
    USER_MESSAGE = "user.message"
    ASSISTANT_MESSAGE = "assistant.message"
    ASSISTANT_CHUNK = "assistant.chunk"  # streaming token/chunk

    # Reasoning
    REASON_STARTED = "reason.started"
    REASON_COMPLETED = "reason.completed"
    REASON_UNKNOWN = "reason.unknown"

    # Agents
    AGENT_STARTED = "agent.started"
    AGENT_STOPPED = "agent.stopped"
    AGENT_STEP = "agent.step"
    AGENT_COMPLETED = "agent.completed"
    AGENT_FAILED = "agent.failed"

    # Tasks (durable Task Engine — Phase 7)
    TASK_CREATED = "task.created"
    TASK_QUEUED = "task.queued"
    TASK_STARTED = "task.started"
    TASK_PROGRESS = "task.progress"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    TASK_CANCELLED = "task.cancelled"

    # Memory / knowledge
    MEMORY_UPDATED = "memory.updated"
    FACT_ADDED = "fact.added"
    GRAPH_UPDATED = "graph.updated"

    # Learning / curriculum
    LEARNING_FINISHED = "learning.finished"
    CURRICULUM_TAUGHT = "curriculum.taught"

    # Tools / security
    TOOL_CALLED = "tool.called"
    TOOL_DENIED = "tool.denied"
    AUDIT_RECORDED = "audit.recorded"

    # Self layers
    SELF_VIEW = "self.view"
    SELF_IMPROVE = "self.improve"
    SELF_MUTATE = "self.mutate"

    # Wildcard (bus support)
    ANY = "*"


@dataclass
class EventPayload:
    """
    Optional structured envelope for future typed publish.
    Existing EventBus still accepts Dict[str, Any]; this is the target shape.
    """

    name: str
    data: Dict[str, Any] = field(default_factory=dict)
    source: str = "system"
    event_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    correlation_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "data": self.data,
            "source": self.source,
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "correlation_id": self.correlation_id,
        }


def make_event_payload(
    name: EventName | str,
    data: Optional[Dict[str, Any]] = None,
    *,
    source: str = "system",
    correlation_id: Optional[str] = None,
) -> EventPayload:
    n = name.value if isinstance(name, EventName) else str(name)
    return EventPayload(
        name=n,
        data=data or {},
        source=source,
        correlation_id=correlation_id,
    )
