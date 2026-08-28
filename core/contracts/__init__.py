"""
Domain contracts for Leon / Zenthon hybrid platform.

Phase 1: stable type surface only. No behavior change to cognitive path.
Existing modules (EventBus, LLMClient, PlanTask, Blackboard) remain authoritative
until later phases adopt these contracts.
"""

from core.contracts.events import (
    EventName,
    EventPayload,
    make_event_payload,
)
from core.contracts.task import (
    Task,
    TaskPriority,
    TaskStatus,
    TaskResult,
    new_task_id,
)
from core.contracts.agent_message import (
    AgentMessage,
    AgentMessageKind,
    AgentRole,
)

__all__ = [
    "EventName",
    "EventPayload",
    "make_event_payload",
    "Task",
    "TaskPriority",
    "TaskStatus",
    "TaskResult",
    "new_task_id",
    "AgentMessage",
    "AgentMessageKind",
    "AgentRole",
]
