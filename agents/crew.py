"""
Multi-Agent Crew – sequential, parallel, and debate modes.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from core.logger import logger
from core.event_bus import event_bus
from agents.manager import agent_manager


@dataclass
class CrewTask:
    description: str
    agent_type: str
    expected_output: str = ""
    allow_experimental: bool = True


@dataclass
class CrewResult:
    success: bool
    outputs: List[Dict[str, Any]] = field(default_factory=list)
    final: Any = None
    mode: str = "sequential"


class Crew:
    """Role-based multi-agent team."""

    def __init__(self, name: str = "LeonCrew"):
        self.name = name
        self.tasks: List[CrewTask] = []

    def add_task(
        self,
        description: str,
        agent_type: str,
        expected_output: str = "",
        *,
        allow_experimental: bool = True,
    ) -> None:
        self.tasks.append(
            CrewTask(description, agent_type, expected_output, allow_experimental)
        )

    def _run_one(
        self,
        task: CrewTask,
        index: int,
        context: str,
    ) -> Dict[str, Any]:
        try:
            agent = agent_manager.create(
                task.agent_type,
                name=f"{self.name}_{task.agent_type}_{index}",
                allow_experimental=task.allow_experimental,
            )
            prompt = task.description
            if context:
                prompt = f"Kontekst:\n{context}\n\nTapşırıq: {task.description}"
            result = agent_manager.run(agent.id, prompt)
            return {
                "task": task.description,
                "agent": task.agent_type,
                "success": result.success,
                "output": result.output,
                "error": result.error,
            }
        except Exception as e:
            return {
                "task": task.description,
                "agent": task.agent_type,
                "success": False,
                "output": None,
                "error": str(e),
            }

    def run(
        self,
        overall_goal: str = "",
        *,
        mode: str = "sequential",
        max_workers: int = 3,
    ) -> CrewResult:
        mode = (mode or "sequential").lower()
        logger.info(f"Crew '{self.name}' mode={mode} tasks={len(self.tasks)}")

        if mode == "parallel":
            return self._run_parallel(overall_goal, max_workers=max_workers)
        if mode == "debate":
            return self._run_debate(overall_goal)
        return self._run_sequential(overall_goal)

    def _run_sequential(self, overall_goal: str) -> CrewResult:
        outputs: List[Dict[str, Any]] = []
        context = overall_goal or ""
        for i, task in enumerate(self.tasks, 1):
            row = self._run_one(task, i, context)
            outputs.append(row)
            if row.get("success") and row.get("output"):
                context = str(row["output"])[:500]
        event_bus.publish(
            "CrewCompleted",
            {"name": self.name, "mode": "sequential", "tasks": len(outputs)},
            source="crew",
        )
        final = outputs[-1].get("output") if outputs else None
        success = all(o.get("success") for o in outputs) if outputs else False
        return CrewResult(success=success, outputs=outputs, final=final, mode="sequential")

    def _run_parallel(self, overall_goal: str, *, max_workers: int = 3) -> CrewResult:
        outputs: List[Dict[str, Any]] = []
        with ThreadPoolExecutor(max_workers=max(1, max_workers)) as pool:
            futs = {
                pool.submit(self._run_one, task, i, overall_goal or ""): i
                for i, task in enumerate(self.tasks, 1)
            }
            ordered: Dict[int, Dict[str, Any]] = {}
            for fut in as_completed(futs):
                idx = futs[fut]
                ordered[idx] = fut.result()
            outputs = [ordered[i] for i in sorted(ordered)]
        event_bus.publish(
            "CrewCompleted",
            {"name": self.name, "mode": "parallel", "tasks": len(outputs)},
            source="crew",
        )
        ok = all(o.get("success") for o in outputs) if outputs else False
        final = {
            "summaries": [
                {"agent": o.get("agent"), "output": str(o.get("output") or "")[:300]}
                for o in outputs
            ]
        }
        return CrewResult(success=ok, outputs=outputs, final=final, mode="parallel")

    def _run_debate(self, overall_goal: str) -> CrewResult:
        """Two agents propose; a third synthesizes (or reason if no third)."""
        if len(self.tasks) < 2:
            return self._run_sequential(overall_goal)

        a, b = self.tasks[0], self.tasks[1]
        out_a = self._run_one(a, 1, overall_goal)
        out_b = self._run_one(b, 2, overall_goal)
        outputs = [out_a, out_b]

        synth_prompt = (
            f"Məqsəd: {overall_goal}\n\n"
            f"Agent A ({a.agent_type}): {out_a.get('output')}\n\n"
            f"Agent B ({b.agent_type}): {out_b.get('output')}\n\n"
            "İkisini birləşdirib yekun cavab ver. Ziddiyyət varsa qeyd et."
        )
        if len(self.tasks) >= 3:
            synth = self._run_one(
                CrewTask(synth_prompt, self.tasks[2].agent_type, allow_experimental=True),
                3,
                "",
            )
        else:
            try:
                from brain.reasoning.engine import reasoning_engine

                r = reasoning_engine.reason(synth_prompt, strategy="cot")
                synth = {
                    "task": "synthesize",
                    "agent": "reasoning",
                    "success": True,
                    "output": r.get("answer"),
                    "error": None,
                }
            except Exception as e:
                synth = {
                    "task": "synthesize",
                    "agent": "reasoning",
                    "success": False,
                    "output": None,
                    "error": str(e),
                }
        outputs.append(synth)
        event_bus.publish(
            "CrewCompleted",
            {"name": self.name, "mode": "debate", "tasks": len(outputs)},
            source="crew",
        )
        return CrewResult(
            success=bool(synth.get("success")),
            outputs=outputs,
            final=synth.get("output"),
            mode="debate",
        )


def default_research_crew(topic: str) -> Crew:
    crew = Crew(name="ResearchBuild")
    crew.add_task(f"'{topic}' mövzusunu araşdır və əsas nöqtələri çıxar", "research")
    crew.add_task(f"'{topic}' üçün praktiki plan yaz", "executor")
    crew.add_task(f"'{topic}' üçün minimal kod skeleti təklif et", "coding")
    return crew


def multimodal_crew(query: str, image_path: Optional[str] = None) -> Crew:
    """Vision + reason + optional voice summary pipeline."""
    crew = Crew(name="Multimodal")
    if image_path:
        crew.add_task(
            f"Şəkli anla: {image_path}. Sual: {query}",
            "vision",
            allow_experimental=True,
        )
    crew.add_task(f"Cavab ver: {query}", "react")
    return crew


def run_crew(
    goal: str,
    tasks: List[Dict[str, str]],
    *,
    mode: str = "sequential",
    name: str = "LeonCrew",
) -> Dict[str, Any]:
    crew = Crew(name=name)
    for t in tasks:
        crew.add_task(
            t.get("description") or t.get("task") or goal,
            t.get("agent_type") or t.get("agent") or "react",
            t.get("expected_output") or "",
        )
    result = crew.run(goal, mode=mode)
    return {
        "success": result.success,
        "mode": result.mode,
        "final": result.final,
        "outputs": result.outputs,
    }
