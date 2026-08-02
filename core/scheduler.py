"""
Scheduler – birdəfəlik, təkrarlanan və prioritetli tasklar.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import threading
import time
import uuid

from core.logger import logger
from core.event_bus import event_bus


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Task:
    name: str
    func: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    priority: int = 5  # 1=highest, 10=lowest
    interval_seconds: Optional[float] = None  # None = one-shot
    run_at: Optional[datetime] = None
    task_id: str = field(default_factory=lambda: str(uuid.uuid4())[:10])
    status: TaskStatus = TaskStatus.PENDING
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    result: Any = None
    error: Optional[str] = None


class Scheduler:
    """Sadə background scheduler."""

    def __init__(self, tick_interval: float = 1.0):
        self._tasks: Dict[str, Task] = {}
        self._lock = threading.RLock()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._tick = tick_interval

    def schedule(
        self,
        name: str,
        func: Callable,
        args: tuple = (),
        kwargs: Optional[Dict] = None,
        priority: int = 5,
        interval_seconds: Optional[float] = None,
        delay_seconds: float = 0,
    ) -> str:
        task = Task(
            name=name,
            func=func,
            args=args,
            kwargs=kwargs or {},
            priority=priority,
            interval_seconds=interval_seconds,
            run_at=datetime.now() + timedelta(seconds=delay_seconds),
            next_run=datetime.now() + timedelta(seconds=delay_seconds),
        )
        with self._lock:
            self._tasks[task.task_id] = task
        logger.info(f"Scheduler: task '{name}' scheduled (id={task.task_id})")
        return task.task_id

    def cancel(self, task_id: str) -> bool:
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return False
            task.status = TaskStatus.CANCELLED
            return True

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True, name="ZenthonScheduler")
        self._thread.start()
        logger.info("Scheduler started.")

    def stop(self) -> None:
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3)
        logger.info("Scheduler stopped.")

    def _loop(self) -> None:
        while self._running:
            now = datetime.now()
            due: List[Task] = []
            with self._lock:
                for task in self._tasks.values():
                    if task.status in (TaskStatus.CANCELLED, TaskStatus.RUNNING):
                        continue
                    if task.next_run and task.next_run <= now:
                        due.append(task)
                due.sort(key=lambda t: t.priority)

            for task in due:
                self._run_task(task)

            time.sleep(self._tick)

    def _run_task(self, task: Task) -> None:
        task.status = TaskStatus.RUNNING
        task.last_run = datetime.now()
        try:
            task.result = task.func(*task.args, **task.kwargs)
            task.status = TaskStatus.DONE
            event_bus.publish(
                "TaskCompleted",
                {"task_id": task.task_id, "name": task.name, "result": str(task.result)[:200]},
                source="scheduler",
            )
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            logger.error(f"Scheduler task '{task.name}' failed: {e}")

        if task.interval_seconds and task.status != TaskStatus.CANCELLED:
            task.next_run = datetime.now() + timedelta(seconds=task.interval_seconds)
            task.status = TaskStatus.PENDING
        else:
            task.next_run = None

    def list_tasks(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [
                {
                    "task_id": t.task_id,
                    "name": t.name,
                    "status": t.status.value,
                    "priority": t.priority,
                    "next_run": t.next_run.isoformat() if t.next_run else None,
                }
                for t in self._tasks.values()
            ]


scheduler = Scheduler()
