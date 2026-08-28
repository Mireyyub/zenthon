"""Durable Task repository on SQLite (Phase 5)."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from core.contracts.task import Task, TaskPriority, TaskResult, TaskStatus, new_task_id
from core.storage.sqlite_db import get_connection, init_schema


def _dumps(obj: Any) -> str:
    return json.dumps(obj if obj is not None else {}, ensure_ascii=False, default=str)


def _loads(s: Optional[str], default: Any = None) -> Any:
    if not s:
        return default if default is not None else {}
    try:
        return json.loads(s)
    except Exception:
        return default if default is not None else {}


def _row_to_task(row: Any) -> Task:
    d = dict(row)
    result = None
    rj = _loads(d.get("result_json"), default=None)
    if isinstance(rj, dict) and rj:
        result = TaskResult.from_dict(rj)
    try:
        status = TaskStatus(d.get("status") or "pending")
    except ValueError:
        status = TaskStatus.PENDING
    try:
        priority = TaskPriority(d.get("priority") or "normal")
    except ValueError:
        priority = TaskPriority.NORMAL
    return Task(
        id=d["id"],
        title=d.get("title") or "",
        goal=d.get("goal") or "",
        action=d.get("action") or "noop",
        params=_loads(d.get("params_json"), {}),
        status=status,
        priority=priority,
        depends_on=[],
        agent_name=d.get("agent_name"),
        plan_id=d.get("plan_id"),
        result=result,
        progress=float(d.get("progress") or 0.0),
        error=d.get("error"),
        created_at=d.get("created_at") or "",
        updated_at=d.get("updated_at") or "",
        started_at=d.get("started_at"),
        finished_at=d.get("finished_at"),
        metadata=_loads(d.get("metadata_json"), {}),
    )


class TaskRepository:
    def __init__(self, path: Optional[str] = None):
        init_schema(path)
        self._path = path

    def _conn(self):
        return get_connection(self._path)

    def save(self, task: Task) -> Task:
        task.touch()
        c = self._conn()
        c.execute(
            """
            INSERT INTO tasks(
                id, title, goal, action, status, priority, params_json, result_json,
                error, agent_name, plan_id, progress, created_at, updated_at,
                started_at, finished_at, metadata_json
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(id) DO UPDATE SET
                title=excluded.title,
                goal=excluded.goal,
                action=excluded.action,
                status=excluded.status,
                priority=excluded.priority,
                params_json=excluded.params_json,
                result_json=excluded.result_json,
                error=excluded.error,
                agent_name=excluded.agent_name,
                plan_id=excluded.plan_id,
                progress=excluded.progress,
                updated_at=excluded.updated_at,
                started_at=excluded.started_at,
                finished_at=excluded.finished_at,
                metadata_json=excluded.metadata_json
            """,
            (
                task.id,
                task.title,
                task.goal,
                task.action,
                task.status.value if hasattr(task.status, "value") else str(task.status),
                task.priority.value if hasattr(task.priority, "value") else str(task.priority),
                _dumps(task.params),
                _dumps(task.result.to_dict() if task.result else None),
                task.error,
                task.agent_name,
                task.plan_id,
                float(task.progress),
                task.created_at,
                task.updated_at,
                task.started_at,
                task.finished_at,
                _dumps(task.metadata),
            ),
        )
        c.commit()
        return task

    def get(self, task_id: str) -> Optional[Task]:
        row = self._conn().execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
        return _row_to_task(row) if row else None

    def list(self, limit: int = 50, status: Optional[str] = None) -> List[Task]:
        if status:
            rows = self._conn().execute(
                "SELECT * FROM tasks WHERE status=? ORDER BY created_at DESC LIMIT ?",
                (status, limit),
            ).fetchall()
        else:
            rows = self._conn().execute(
                "SELECT * FROM tasks ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
        return [_row_to_task(r) for r in rows]

    def create(
        self,
        title: str,
        *,
        goal: str = "",
        action: str = "reason",
        params: Optional[Dict] = None,
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
        return self.save(task)

    def delete(self, task_id: str) -> bool:
        c = self._conn()
        cur = c.execute("DELETE FROM tasks WHERE id=?", (task_id,))
        c.commit()
        return cur.rowcount > 0
