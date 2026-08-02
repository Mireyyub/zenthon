"""Base Agent interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime
import uuid

from core.logger import logger
from core.event_bus import event_bus


@dataclass
class AgentResult:
    success: bool
    output: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseAgent(ABC):
    """Bütün agentlərin baza sinifi."""

    def __init__(self, name: str, description: str = ""):
        self.id = str(uuid.uuid4())[:10]
        self.name = name
        self.description = description
        self.created_at = datetime.now()
        self._running = False

    @abstractmethod
    def run(self, task: str, context: Optional[Dict[str, Any]] = None) -> AgentResult:
        """Əsas icra metodu."""
        ...

    def start(self) -> None:
        self._running = True
        event_bus.publish("AgentStarted", {"agent_id": self.id, "name": self.name}, source="agents")

    def stop(self) -> None:
        self._running = False
        event_bus.publish("AgentStopped", {"agent_id": self.id, "name": self.name}, source="agents")

    def info(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "running": self._running,
            "created_at": self.created_at.isoformat(),
        }

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r}, id={self.id})"
