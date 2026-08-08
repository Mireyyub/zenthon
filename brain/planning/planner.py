"""
Minimal Planner – create / list / update / run / replan.
Includes self_improve action.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.logger import logger
from core.persistence import write_json, read_json
from brain.planning.schema import Plan, PlanTask, new_plan_id, new_task_id


def _plans_dir() -> Path:
    try:
        from core.config import config

        d = Path(config.path.leon_dir) / "plans"
    except Exception:
        d = Path("data/leon/plans")
    d.mkdir(parents=True, exist_ok=True)
    return d


class Planner:
    def __init__(self, directory: Optional[Path | str] = None):
        self.dir = Path(directory) if directory else _plans_dir()
        self.dir.mkdir(parents=True, exist_ok=True)
        self._cache: Dict[str, Plan] = {}

    def create(
        self,
        goal: str,
        tasks: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Plan:
        plan = Plan(
            id=new_plan_id(),
            goal=goal,
            tasks=[],
            status="draft",
            metadata=metadata or {},
        )
        for t in tasks or []:
            if isinstance(t, PlanTask):
                plan.tasks.append(t)
            else:
                td = dict(t)
                td.setdefault("id", new_task_id())
                plan.tasks.append(PlanTask.from_dict(td))
        self._refresh_ready(plan)
        self.save(plan)
        logger.info(f"Planner: created {plan.id} goal={goal[:60]}")
        return plan

    def get(self, plan_id: str) -> Optional[Plan]:
        if plan_id in self._cache:
            return self._cache[plan_id]
        path = self.dir / f"{plan_id}.json"
        data = read_json(path, default=None)
        if not data:
            return None
        plan = Plan.from_dict(data)
        self._cache[plan_id] = plan
        return plan

    def list_plans(self) -> List[Dict[str, Any]]:
        out = []
        for p in sorted(self.dir.glob("P-*.json"), reverse=True):
            data = read_json(p, default={})
            if not data:
                continue
            out.append(
                {
                    "id": data.get("id"),
                    "goal": data.get("goal"),
                    "status": data.get("status"),
                    "version": data.get("version"),
                    "tasks": len(data.get("tasks") or []),
                    "updated_at": data.get("updated_at"),
                }
            )
        return out

    def update_task(
        self,
        plan_id: str,
        task_id: str,
        *,
        status: Optional[str] = None,
        result: Any = None,
        error: Optional[str] = None,
        title: Optional[str] = None,
    ) -> Optional[Plan]:
        plan = self.get(plan_id)
        if not plan:
            return None
        for t in plan.tasks:
            if t.id == task_id:
                if status:
                    t.status = status
                if result is not None:
                    t.result = result
                if error is not None:
                    t.error = error
                if title is not None:
                    t.title = title
                break
        else:
            return None
        self._refresh_ready(plan)
        self._update_plan_status(plan)
        plan.updated_at = datetime.now().isoformat()
        self.save(plan)
        return plan

    def add_task(self, plan_id: str, task: Dict[str, Any]) -> Optional[Plan]:
        plan = self.get(plan_id)
        if not plan:
            return None
        td = dict(task)
        td.setdefault("id", new_task_id())
        plan.tasks.append(PlanTask.from_dict(td))
        plan.version += 1
        self._refresh_ready(plan)
        plan.updated_at = datetime.now().isoformat()
        self.save(plan)
        return plan

    def save(self, plan: Plan) -> None:
        plan.updated_at = datetime.now().isoformat()
        write_json(self.dir / f"{plan.id}.json", plan.to_dict())
        self._cache[plan.id] = plan

    def ordered_tasks(self, plan: Plan) -> List[PlanTask]:
        by_id = {t.id: t for t in plan.tasks}
        pending = set(by_id)
        result: List[PlanTask] = []
        while pending:
            ready = [
                tid
                for tid in pending
                if all(d not in pending for d in (by_id[tid].depends_on or []))
            ]
            if not ready:
                logger.warning(f"Planner: cycle or missing dep in {plan.id}")
                for tid in list(pending):
                    result.append(by_id[tid])
                break
            ready.sort()
            for tid in ready:
                pending.remove(tid)
                result.append(by_id[tid])
        return result

    def _refresh_ready(self, plan: Plan) -> None:
        done_ids = {t.id for t in plan.tasks if t.status == "done"}
        for t in plan.tasks:
            if t.status in ("done", "failed", "skipped", "running"):
                continue
            deps_ok = all(d in done_ids for d in (t.depends_on or []))
            t.status = "ready" if deps_ok else "pending"

    def _update_plan_status(self, plan: Plan) -> None:
        statuses = [t.status for t in plan.tasks]
        if not statuses:
            plan.status = "draft"
            return
        if all(s == "done" for s in statuses):
            plan.status = "completed"
        elif any(s == "failed" for s in statuses):
            plan.status = "failed"
        elif any(s in ("running", "ready", "done") for s in statuses):
            plan.status = "active"
        else:
            plan.status = "draft"

    def run(self, plan_id: str, max_tasks: Optional[int] = None) -> Dict[str, Any]:
        plan = self.get(plan_id)
        if not plan:
            return {"error": f"plan not found: {plan_id}"}
        plan.status = "active"
        self.save(plan)

        executed = []
        ordered = self.ordered_tasks(plan)
        count = 0
        for task in ordered:
            if max_tasks is not None and count >= max_tasks:
                break
            if task.status in ("done", "skipped"):
                continue
            if any(
                self._task_status(plan, d) not in ("done", "skipped")
                for d in (task.depends_on or [])
            ):
                continue
            task.status = "running"
            self.save(plan)
            try:
                result = self._execute_task(task)
                task.result = result
                task.status = "done"
                task.error = None
            except Exception as e:
                task.status = "failed"
                task.error = str(e)
                logger.warning(f"Planner task failed {task.id}: {e}")
            executed.append(task.to_dict())
            count += 1
            self._refresh_ready(plan)
            self._update_plan_status(plan)
            self.save(plan)
            if task.status == "failed":
                break

        return {
            "plan_id": plan.id,
            "status": plan.status,
            "executed": executed,
            "plan": plan.to_dict(),
        }

    def _task_status(self, plan: Plan, task_id: str) -> str:
        for t in plan.tasks:
            if t.id == task_id:
                return t.status
        return "missing"

    def _execute_task(self, task: PlanTask) -> Any:
        action = (task.action or "noop").lower()
        params = task.params or {}

        if action == "noop":
            return {"ok": True, "note": "noop"}

        if action == "teach":
            from curriculum import CurriculumEngine

            eng = CurriculumEngine()
            return eng.teach(
                params.get("lesson_id", "000001"), volume_id=params.get("volume_id")
            )

        if action == "teach_volume":
            from curriculum import CurriculumEngine

            return CurriculumEngine().teach_volume(params.get("volume_id", "01"))

        if action == "reason":
            from brain.reasoning.engine import reasoning_engine

            q = params.get("query") or task.title
            return reasoning_engine.reason(q, strategy=params.get("strategy", "auto"))

        if action == "retrieve":
            from memory.retrieve import retrieve

            return retrieve(params.get("query") or task.title, top_k=params.get("top_k", 5))

        if action == "agent":
            from agents.manager import agent_manager

            atype = params.get("type", "react")
            agent = agent_manager.create(
                atype, allow_experimental=params.get("experimental", False)
            )
            res = agent_manager.run(agent.id, params.get("task") or task.title)
            return {"success": res.success, "output": res.output, "error": res.error}

        if action == "save_state":
            from core.bootstrap import save_state

            return save_state(params.get("name", "plan"))

        if action == "self_improve":
            from brain.self_improve import improve

            vols = params.get("volumes")
            return improve(volumes=vols, dry_run=bool(params.get("dry_run", False)))

        if action == "eval_volume":
            from curriculum import CurriculumEngine

            return CurriculumEngine().run_eval(params.get("volume_id", "01"))

        raise ValueError(f"unknown action: {action}")

    def replan(
        self,
        plan_id: str,
        *,
        reason: str = "user",
        retry_failed: bool = True,
        extra_tasks: Optional[List[Dict[str, Any]]] = None,
    ) -> Optional[Plan]:
        plan = self.get(plan_id)
        if not plan:
            return None
        if retry_failed:
            for t in plan.tasks:
                if t.status == "failed":
                    t.status = "pending"
                    t.error = None
                    t.result = None
        for t in extra_tasks or []:
            td = dict(t)
            td.setdefault("id", new_task_id())
            plan.tasks.append(PlanTask.from_dict(td))
        plan.version += 1
        plan.metadata["last_replan"] = {
            "reason": reason,
            "at": datetime.now().isoformat(),
            "version": plan.version,
        }
        self._refresh_ready(plan)
        plan.status = "active"
        plan.updated_at = datetime.now().isoformat()
        self.save(plan)
        return plan


def curriculum_learn_plan(volume_id: str = "01") -> Plan:
    planner = Planner()
    t1, t2, t3, t4 = new_task_id(), new_task_id(), new_task_id(), new_task_id()
    return planner.create(
        goal=f"Volume {volume_id} öyrən və qiymətləndir",
        metadata={"template": "curriculum_learn", "volume_id": volume_id},
        tasks=[
            {
                "id": t1,
                "title": f"Teach volume {volume_id}",
                "action": "teach_volume",
                "params": {"volume_id": volume_id},
            },
            {
                "id": t2,
                "title": "Save state after teach",
                "action": "save_state",
                "params": {"name": f"after_vol_{volume_id}"},
                "depends_on": [t1],
            },
            {
                "id": t3,
                "title": "Sample reason check",
                "action": "reason",
                "params": {"query": "Daş mövcuddurmu?"},
                "depends_on": [t1],
            },
            {
                "id": t4,
                "title": "Retrieve foundation concepts",
                "action": "retrieve",
                "params": {"query": "obyekt varlıq", "top_k": 5},
                "depends_on": [t1],
            },
        ],
    )


def self_improve_plan(volumes: Optional[List[str]] = None) -> Plan:
    """Plan that runs Leon's self-improvement cycle."""
    planner = Planner()
    t1, t2 = new_task_id(), new_task_id()
    return planner.create(
        goal="Özünü qiymətləndir və bilik boşluqlarını bağla",
        metadata={"template": "self_improve", "volumes": volumes or ["01", "02"]},
        tasks=[
            {
                "id": t1,
                "title": "Self-improve cycle",
                "action": "self_improve",
                "params": {"volumes": volumes or ["01", "02"]},
            },
            {
                "id": t2,
                "title": "Save after improve",
                "action": "save_state",
                "params": {"name": "post_self_improve"},
                "depends_on": [t1],
            },
        ],
    )


planner = Planner()
