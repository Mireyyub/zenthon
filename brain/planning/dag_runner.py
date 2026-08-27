"""
brain/planning/dag_runner.py — Async DAG execution engine.
Source: Drive Leon.təlim dag_runner.py, adapted for zenthon.
Pure asyncio + topological waves. No extra deps beyond stdlib.
"""
from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from core.logger import logger


@dataclass
class DAGNode:
    id: str
    label: str
    func: Callable
    depends_on: list[str] = field(default_factory=list)
    timeout_s: int = 60
    status: str = "pending"  # pending|running|done|failed|skipped
    result: Any = None
    error: Optional[str] = None
    start_time: float = 0.0
    end_time: float = 0.0

    @property
    def duration_s(self) -> float:
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0.0


@dataclass
class DAGRun:
    run_id: str
    nodes: dict[str, DAGNode] = field(default_factory=dict)
    start_time: float = field(default_factory=time.time)
    end_time: float = 0.0
    status: str = "pending"

    @property
    def duration_s(self) -> float:
        end = self.end_time or time.time()
        return end - self.start_time

    @property
    def success_count(self) -> int:
        return sum(1 for n in self.nodes.values() if n.status == "done")

    @property
    def fail_count(self) -> int:
        return sum(1 for n in self.nodes.values() if n.status == "failed")

    def summary(self) -> str:
        total = len(self.nodes)
        return (
            f"DAG {self.run_id}: {self.success_count}/{total} uğurlu | "
            f"{self.fail_count} uğursuz | {self.duration_s:.1f}s"
        )


class DAGRunner:
    """
    Asyncio DAG runner with topological waves, per-node timeout,
    and partial execution (failed nodes do not block independent ones).
    """

    def __init__(self) -> None:
        self._runs: list[DAGRun] = []

    async def run_dag(
        self,
        nodes: list[DAGNode],
        run_id: Optional[str] = None,
        on_event: Optional[Callable] = None,
    ) -> DAGRun:
        run_id = run_id or str(uuid.uuid4())[:8]
        dag_run = DAGRun(run_id=run_id, nodes={n.id: n for n in nodes})
        self._runs.append(dag_run)

        logger.info(f"[DAGRunner] Başladı [{run_id}]: {len(nodes)} node")
        dag_run.status = "running"

        waves = self._topological_waves(nodes)
        logger.info(f"[DAGRunner] {len(waves)} paralel dalğa")

        done_results: dict[str, Any] = {}

        for wave_idx, wave in enumerate(waves, 1):
            logger.info(f"[DAGRunner] Dalğa {wave_idx}/{len(waves)}: {[n.id for n in wave]}")
            if on_event:
                on_event({"event": "wave_start", "wave": wave_idx, "nodes": [n.id for n in wave]})

            tasks = []
            for node in wave:
                node.status = "running"
                node.start_time = time.time()
                tasks.append(self._run_node(node, done_results, on_event))

            wave_results = await asyncio.gather(*tasks, return_exceptions=True)

            for node, res in zip(wave, wave_results):
                node.end_time = time.time()
                if isinstance(res, Exception):
                    node.status = "failed"
                    node.error = str(res)
                    logger.error(f"[DAGRunner] [{node.id}] Xəta: {res}")
                else:
                    done_results[node.id] = node.result

        dag_run.end_time = time.time()
        dag_run.status = "done" if dag_run.fail_count == 0 else "partial"
        logger.info(f"[DAGRunner] Tamamlandı: {dag_run.summary()}")

        if on_event:
            on_event({"event": "dag_done", "summary": dag_run.summary()})

        return dag_run

    async def _run_node(
        self,
        node: DAGNode,
        done_results: dict,
        on_event: Optional[Callable],
    ) -> None:
        dep_results = {dep_id: done_results.get(dep_id) for dep_id in node.depends_on}

        try:
            if asyncio.iscoroutinefunction(node.func):
                result = await asyncio.wait_for(
                    node.func(dep_results=dep_results),
                    timeout=node.timeout_s,
                )
            else:
                loop = asyncio.get_event_loop()
                result = await asyncio.wait_for(
                    loop.run_in_executor(None, lambda: node.func(dep_results=dep_results)),
                    timeout=node.timeout_s,
                )

            node.result = result
            node.status = "done"

            if on_event:
                on_event({
                    "event": "node_done",
                    "node_id": node.id,
                    "label": node.label,
                    "duration": node.duration_s,
                })

        except asyncio.TimeoutError:
            node.status = "failed"
            node.error = f"Timeout: {node.timeout_s}s keçdi"
            logger.error(f"[DAGRunner] [{node.id}] Timeout")
            if on_event:
                on_event({"event": "node_timeout", "node_id": node.id})

        except Exception as e:
            node.status = "failed"
            node.error = str(e)
            raise

    def _topological_waves(self, nodes: list[DAGNode]) -> list[list[DAGNode]]:
        """Kahn-style wave partitioning."""
        done_ids: set[str] = set()
        waves: list[list[DAGNode]] = []

        while True:
            wave = [
                n for n in nodes
                if n.id not in done_ids and all(dep in done_ids for dep in n.depends_on)
            ]
            if not wave:
                break
            waves.append(wave)
            for n in wave:
                done_ids.add(n.id)

        remaining = [n for n in nodes if n.id not in done_ids]
        if remaining:
            logger.warning(
                f"[DAGRunner] Cycle / orphan nodes sequential: {[n.id for n in remaining]}"
            )
            waves.append(remaining)

        return waves

    def run_sync(
        self,
        nodes: list[DAGNode],
        run_id: Optional[str] = None,
        on_event: Optional[Callable] = None,
    ) -> DAGRun:
        """Sync wrapper for non-async contexts."""
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self.run_dag(nodes, run_id, on_event))
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(
                lambda: asyncio.run(self.run_dag(nodes, run_id, on_event))
            ).result()

    def get_history(self) -> list[dict]:
        return [
            {
                "run_id": r.run_id,
                "status": r.status,
                "duration": f"{r.duration_s:.1f}s",
                "nodes": len(r.nodes),
                "success": r.success_count,
                "failed": r.fail_count,
            }
            for r in self._runs
        ]
