from __future__ import annotations

"""
Task Blackboard — shared structured memory for multi-agent runs.
Source: Drive Leon.təlim (Local AGI blackboard.py), adapted for Leon/zenthon.
"""

import threading
import time
from dataclasses import dataclass, field
from typing import Any

from core.logger import logger


@dataclass
class Fact:
    content: str
    source: str
    confidence: float = 1.0
    timestamp: float = field(default_factory=time.time)


@dataclass
class Artifact:
    kind: str
    reference: str
    source: str
    timestamp: float = field(default_factory=time.time)


@dataclass
class Warning:
    message: str
    severity: str
    source: str
    timestamp: float = field(default_factory=time.time)


@dataclass
class Decision:
    agent: str
    statement: str
    confidence: float = 1.0
    timestamp: float = field(default_factory=time.time)


@dataclass
class Reflection:
    reflecting_agent: str
    about_agent: str
    about_statement: str
    reaction: str
    content: str
    timestamp: float = field(default_factory=time.time)


class TaskBlackboard:
    """Thread-safe shared state for one task execution."""

    def __init__(self, task_id: str, original_task: str = ""):
        self.task_id = task_id
        self.original_task = original_task
        self._lock = threading.Lock()
        self._facts: list[Fact] = []
        self._artifacts: list[Artifact] = []
        self._warnings: list[Warning] = []
        self._decisions: list[Decision] = []
        self._reflections: list[Reflection] = []
        self._scratch: dict[str, Any] = {}
        self._created_at = time.time()

    def add_fact(self, content: str, source: str, confidence: float = 1.0) -> None:
        with self._lock:
            self._facts.append(Fact(content=content[:500], source=source, confidence=confidence))

    def add_artifact(self, kind: str, reference: str, source: str) -> None:
        with self._lock:
            self._artifacts.append(Artifact(kind=kind, reference=reference, source=source))

    def add_warning(self, message: str, severity: str, source: str) -> None:
        with self._lock:
            self._warnings.append(Warning(message=message[:300], severity=severity, source=source))

    def add_decision(self, agent: str, statement: str, confidence: float = 1.0) -> None:
        with self._lock:
            self._decisions.append(
                Decision(agent=agent, statement=statement[:400], confidence=confidence)
            )

    def add_reflection(
        self,
        reflecting_agent: str,
        about_agent: str,
        about_statement: str,
        reaction: str,
        content: str,
    ) -> None:
        with self._lock:
            self._reflections.append(
                Reflection(
                    reflecting_agent=reflecting_agent,
                    about_agent=about_agent,
                    about_statement=about_statement[:200],
                    reaction=reaction,
                    content=content[:400],
                )
            )

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            self._scratch[key] = value

    def get(self, key: str, default=None) -> Any:
        with self._lock:
            return self._scratch.get(key, default)

    def facts_text(self, max_items: int = 8) -> str:
        with self._lock:
            recent = self._facts[-max_items:]
        if not recent:
            return ""
        return "Məlum faktlar:\n" + "\n".join(f"  - [{f.source}] {f.content}" for f in recent)

    def decisions_text(self, max_items: int = 6) -> str:
        with self._lock:
            recent = self._decisions[-max_items:]
        if not recent:
            return ""
        return "Digər agentlərin qərarları:\n" + "\n".join(
            f"  - [{d.agent}] {d.statement} (əminlik: {d.confidence:.0%})" for d in recent
        )

    def reflections_text(self, max_items: int = 4) -> str:
        with self._lock:
            recent = self._reflections[-max_items:]
        if not recent:
            return ""
        icon = {"agree": "✓", "concern": "⚠", "question": "?"}
        return "Agent refleksiyaları:\n" + "\n".join(
            f"  - [{r.reflecting_agent}→{r.about_agent}] "
            f"{icon.get(r.reaction, '·')} {r.content}"
            for r in recent
        )

    def agent_context_block(self) -> str:
        parts = [self.facts_text(), self.decisions_text(), self.reflections_text()]
        parts = [p for p in parts if p]
        return "\n\n".join(parts)

    def artifacts_summary(self) -> list[dict]:
        with self._lock:
            return [
                {"kind": a.kind, "ref": a.reference, "source": a.source}
                for a in self._artifacts
            ]

    def has_blocking_warnings(self) -> bool:
        with self._lock:
            return any(w.severity == "block" for w in self._warnings)

    def has_any_warning(self) -> bool:
        with self._lock:
            return any(w.severity in ("block", "warn") for w in self._warnings)

    def warnings_text(self) -> str:
        with self._lock:
            if not self._warnings:
                return ""
            lines = [f"  ⚠ [{w.severity}] {w.message}" for w in self._warnings]
        return "Qeydlər:\n" + "\n".join(lines)

    def to_dict(self) -> dict:
        with self._lock:
            return {
                "task_id": self.task_id,
                "facts": len(self._facts),
                "artifacts": len(self._artifacts),
                "warnings": len(self._warnings),
                "decisions": len(self._decisions),
                "reflections": len(self._reflections),
                "age_s": round(time.time() - self._created_at, 2),
            }

    def __repr__(self) -> str:
        d = self.to_dict()
        return (
            f"<Blackboard {d['task_id']} facts={d['facts']} "
            f"decisions={d['decisions']} reflections={d['reflections']}>"
        )
