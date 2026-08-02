"""Goals System – məqsəd idarəetməsi və izləmə."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid


class GoalStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


@dataclass
class Goal:
    description: str
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:10])
    status: GoalStatus = GoalStatus.ACTIVE
    priority: int = 5
    plan: List[str] = field(default_factory=list)
    progress: float = 0.0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)


class GoalManager:
    def __init__(self):
        self._goals: Dict[str, Goal] = {}
        self._active_id: Optional[str] = None

    def create(self, description: str, priority: int = 5, plan: Optional[List[str]] = None) -> Goal:
        goal = Goal(description=description, priority=priority, plan=plan or [])
        self._goals[goal.id] = goal
        if self._active_id is None:
            self._active_id = goal.id
        return goal

    def set_active(self, goal_id: str) -> None:
        if goal_id not in self._goals:
            raise KeyError(goal_id)
        self._active_id = goal_id

    def get_active(self) -> Optional[Goal]:
        if self._active_id:
            return self._goals.get(self._active_id)
        return None

    def update_progress(self, goal_id: str, progress: float) -> None:
        g = self._goals[goal_id]
        g.progress = max(0.0, min(1.0, progress))
        if g.progress >= 1.0:
            g.status = GoalStatus.COMPLETED

    def complete(self, goal_id: str) -> None:
        self._goals[goal_id].status = GoalStatus.COMPLETED
        self._goals[goal_id].progress = 1.0

    def list_goals(self, status: Optional[GoalStatus] = None) -> List[Goal]:
        goals = list(self._goals.values())
        if status:
            goals = [g for g in goals if g.status == status]
        return sorted(goals, key=lambda g: g.priority)
