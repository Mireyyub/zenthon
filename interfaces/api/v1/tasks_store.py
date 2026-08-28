"""
Task store for /api/v1/tasks (Phase 5 — SQLite durable).

Falls back to in-memory only if SQLite init fails (tests / broken FS).
"""

from __future__ import annotations

import threading
from typing import Dict, List, Optional

from core.contracts.task import Task, TaskPriority, TaskStatus, new_task_id
from core.logger import logger


class _MemoryTaskStore:
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


class TaskStore:
    """SQLite-backed task store with memory fallback."""

    def __init__(self) -> None:
        self._durable = True
        self._repo = None
        self._mem = _MemoryTaskStore()
        try:
            from core.storage.task_repo import TaskRepository

            self._repo = TaskRepository()
            self._durable = True
        except Exception as e:
            logger.warning(f"TaskStore: SQLite unavailable, memory only: {e}")
            self._durable = False

    @property
    def durable(self) -> bool:
        return bool(self._durable and self._repo is not None)

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
        if self._repo is not None:
            try:
                return self._repo.create(
                    title,
                    goal=goal,
                    action=action,
                    params=params,
                    priority=priority,
                    agent_name=agent_name,
                )
            except Exception as e:
                logger.warning(f"TaskStore.create SQLite fail → memory: {e}")
        return self._mem.create(
            title, goal=goal, action=action, params=params, priority=priority, agent_name=agent_name
        )

    def get(self, task_id: str) -> Optional[Task]:
        if self._repo is not None:
            try:
                t = self._repo.get(task_id)
                if t is not None:
                    return t
            except Exception:
                pass
        return self._mem.get(task_id)

    def list(self, limit: int = 50) -> List[Task]:
        if self._repo is not None:
            try:
                return self._repo.list(limit=limit)
            except Exception as e:
                logger.warning(f"TaskStore.list SQLite fail: {e}")
        return self._mem.list(limit=limit)

    def update(self, task: Task) -> Task:
        if self._repo is not None:
            try:
                return self._repo.save(task)
            except Exception as e:
                logger.warning(f"TaskStore.update SQLite fail: {e}")
        return self._mem.update(task)


task_store = TaskStore()
