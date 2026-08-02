"""
Multi-Agent Crew – role-based əməkdaşlıq (CrewAI üslubunda sadələşdirilmiş).

Bir neçə agent eyni məqsəd üçün ardıcıl və ya sadə parallel işləyir.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from core.logger import logger
from core.event_bus import event_bus
from agents.manager import agent_manager
from agents.base import AgentResult


@dataclass
class CrewTask:
    description: str
    agent_type: str
    expected_output: str = ""


@dataclass
class CrewResult:
    success: bool
    outputs: List[Dict[str, Any]] = field(default_factory=list)
    final: Any = None


class Crew:
    """Role-based multi-agent team."""

    def __init__(self, name: str = "ZenthonCrew"):
        self.name = name
        self.tasks: List[CrewTask] = []

    def add_task(self, description: str, agent_type: str, expected_output: str = "") -> None:
        self.tasks.append(CrewTask(description, agent_type, expected_output))

    def run(self, overall_goal: str = "") -> CrewResult:
        logger.info(f"Crew '{self.name}' starting ({len(self.tasks)} tasks)")
        outputs = []
        context_so_far = overall_goal

        for i, task in enumerate(self.tasks, 1):
            logger.info(f"  Crew task {i}: [{task.agent_type}] {task.description[:60]}")
            try:
                agent = agent_manager.create(task.agent_type, name=f"{self.name}_{task.agent_type}_{i}")
                prompt = task.description
                if context_so_far:
                    prompt = f"Kontekst: {context_so_far}\n\nTapşırıq: {task.description}"
                result = agent_manager.run(agent.id, prompt)
                outputs.append({
                    "task": task.description,
                    "agent": task.agent_type,
                    "success": result.success,
                    "output": result.output,
                })
                if result.success and result.output:
                    context_so_far = str(result.output)[:400]
            except Exception as e:
                outputs.append({
                    "task": task.description,
                    "agent": task.agent_type,
                    "success": False,
                    "output": str(e),
                })

        event_bus.publish("CrewCompleted", {"name": self.name, "tasks": len(outputs)}, source="crew")
        final = outputs[-1]["output"] if outputs else None
        success = all(o.get("success") for o in outputs) if outputs else False
        return CrewResult(success=success, outputs=outputs, final=final)


def default_research_crew(topic: str) -> Crew:
    """Hazır research → plan → code crew."""
    crew = Crew(name="ResearchBuild")
    crew.add_task(f"'{topic}' mövzusunu araşdır və əsas nöqtələri çıxar", "research")
    crew.add_task(f"'{topic}' üçün praktiki plan yaz", "executor")
    crew.add_task(f"'{topic}' üçün minimal kod skeleti təklif et", "coding")
    return crew
