"""
In-memory Task store for /api/v1/tasks (Phase 3).

Durable SQLite Task Engine is Phase 5–7. This store is process-local,
JSON-serializable via core.contracts.Task, and safe for prototype UI.
"""

from __future__ import annotations

import threading
from typing import Dict, List, Optional

from core.contracts.task import Task, TaskPriority, TaskStatus, new_task_id


class TaskStore:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._tasks: Dict[str, Task] = {}

    def create(
        self,
        title: str,
        *,
        goal: str = "",
        action: str = "reason",
        params: Optional[dict] = None,
        priority: str = "normal",
        agent_name: Optional[str] = None,
    ) -> Task:
        try:
            prio = TaskPriority(priority)
        except ValueError:
            prio = TaskPriority.NORMAL
        task = Task(
            id=new_task_id(),
            title=title,
            goal=goal or title,
            action=action,
            params=dict(params or {}),
            status=TaskStatus.PENDING,
            priority=prio,
            agent_name=agent_name,
        )
        with self._lock:
            self._tasks[task.id] = task
        return task

    def get(self, task_id: str) -> Optional[Task]:
        with self._lock:
            return self._tasks.get(task_id)

    def list(self, limit: int = 50) -> List[Task]:
        with self._lock:
            items = list(self._tasks.values())
        items.sort(key=lambda t: t.created_at, reverse=True)
        return items[:limit]

    def update(self, task: Task) -> Task:
        task.touch()
        with self._lock:
            self._tasks[task.id] = task
        return task


task_store = TaskStore()
