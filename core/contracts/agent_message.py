"""
Agent message protocol for multi-agent / blackboard communication.

Complements agents/blackboard.py (TaskBlackboard stays operational).
This module defines the message shape agents exchange and that the
future AgentManager + WebSocket layers can serialize.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid


class AgentRole(str, Enum):
    PLANNER = "planner"
    REASONER = "reasoner"
    CRITIC = "critic"
    EXECUTOR = "executor"
    MEMORY = "memory"
    RESEARCH = "research"
    CODING = "coding"
    REACT = "react"
    VISION = "vision"
    VOICE = "voice"
    COORDINATOR = "coordinator"
    USER = "user"
    SYSTEM = "system"


class AgentMessageKind(str, Enum):
    TASK = "task"
    OBSERVATION = "observation"
    THOUGHT = "thought"
    ACTION = "action"
    RESULT = "result"
    DECISION = "decision"
    CRITIQUE = "critique"
    REFLECTION = "reflection"
    FACT = "fact"
    WARNING = "warning"
    ARTIFACT = "artifact"
    ERROR = "error"
    STATUS = "status"


def new_message_id() -> str:
    return "AM-" + uuid.uuid4().hex[:10]


@dataclass
class AgentMessage:
    """Single structured message between agents or agent ↔ system."""

    id: str
    kind: AgentMessageKind
    role: AgentRole
    content: str
    agent_name: str = ""
    task_id: Optional[str] = None
    confidence: float = 1.0
    parent_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind.value if isinstance(self.kind, AgentMessageKind) else self.kind,
            "role": self.role.value if isinstance(self.role, AgentRole) else self.role,
            "content": self.content,
            "agent_name": self.agent_name,
            "task_id": self.task_id,
            "confidence": self.confidence,
            "parent_id": self.parent_id,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "AgentMessage":
        kind_raw = d.get("kind") or "observation"
        role_raw = d.get("role") or "system"
        try:
            kind = AgentMessageKind(kind_raw)
        except ValueError:
            kind = AgentMessageKind.OBSERVATION
        try:
            role = AgentRole(role_raw)
        except ValueError:
            role = AgentRole.SYSTEM
        return cls(
            id=d.get("id") or new_message_id(),
            kind=kind,
            role=role,
            content=str(d.get("content") or "")[:4000],
            agent_name=str(d.get("agent_name") or ""),
            task_id=d.get("task_id"),
            confidence=float(d.get("confidence") if d.get("confidence") is not None else 1.0),
            parent_id=d.get("parent_id"),
            metadata=dict(d.get("metadata") or {}),
            timestamp=d.get("timestamp") or datetime.now().isoformat(),
        )

    @classmethod
    def make(
        cls,
        kind: AgentMessageKind | str,
        role: AgentRole | str,
        content: str,
        *,
        agent_name: str = "",
        task_id: Optional[str] = None,
        confidence: float = 1.0,
        parent_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "AgentMessage":
        if not isinstance(kind, AgentMessageKind):
            try:
                kind = AgentMessageKind(str(kind))
            except ValueError:
                kind = AgentMessageKind.OBSERVATION
        if not isinstance(role, AgentRole):
            try:
                role = AgentRole(str(role))
            except ValueError:
                role = AgentRole.SYSTEM
        return cls(
            id=new_message_id(),
            kind=kind,
            role=role,
            content=content[:4000],
            agent_name=agent_name,
            task_id=task_id,
            confidence=max(0.0, min(1.0, confidence)),
            parent_id=parent_id,
            metadata=metadata or {},
        )
