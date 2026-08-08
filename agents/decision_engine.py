"""
agents/decision_engine.py — Multi-criteria decision matrix.
Source: Drive Leon.təlim decision_engine.py, adapted for zenthon.
Pure Python, no extra deps. Used by planner / crew for alternative selection.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from core.logger import logger


@dataclass
class Alternative:
    id: str
    description: str
    scores: dict[str, float] = field(default_factory=dict)
    weighted: float = 0.0
    rationale: str = ""


@dataclass
class DecisionCriteria:
    accuracy: float = 0.30
    latency: float = 0.20
    compute: float = 0.20
    reliability: float = 0.20
    complexity: float = 0.10

    def validate(self) -> bool:
        return abs(sum(vars(self).values()) - 1.0) < 0.01

    @classmethod
    def for_task_type(cls, task_type: str) -> "DecisionCriteria":
        presets = {
            "critical": cls(accuracy=0.45, latency=0.10, compute=0.15, reliability=0.25, complexity=0.05),
            "realtime": cls(accuracy=0.20, latency=0.40, compute=0.20, reliability=0.15, complexity=0.05),
            "research": cls(accuracy=0.40, latency=0.10, compute=0.10, reliability=0.25, complexity=0.15),
            "simple":   cls(accuracy=0.25, latency=0.25, compute=0.25, reliability=0.20, complexity=0.05),
        }
        return presets.get(task_type, cls())


@dataclass
class DecisionResult:
    winner: Alternative
    alternatives: list[Alternative]
    criteria: DecisionCriteria
    task_type: str
    margin: float

    def report(self) -> str:
        lines = [
            f"Seçilən: [{self.winner.id}] {self.winner.description}",
            f"Çəkili skor: {self.winner.weighted:.3f}",
            f"Üstünlük: +{self.margin:.1%}",
            "",
            "Alternativlər:",
        ]
        for alt in sorted(self.alternatives, key=lambda a: a.weighted, reverse=True):
            marker = "→" if alt.id == self.winner.id else " "
            lines.append(f"  {marker} [{alt.id}] {alt.description[:50]:<50} {alt.weighted:.3f}")
        return "\n".join(lines)


class DecisionEngine:
    """Weighted multi-criteria decision matrix (accuracy / latency / compute / reliability / complexity)."""

    def __init__(self) -> None:
        self._decisions: list[DecisionResult] = []

    def decide(
        self,
        alternatives: list[dict],
        task_type: str = "simple",
        custom_criteria: Optional[DecisionCriteria] = None,
    ) -> DecisionResult:
        if len(alternatives) < 2:
            raise ValueError("Ən az 2 alternativ lazımdır")

        criteria = custom_criteria or DecisionCriteria.for_task_type(task_type)
        crit_dict = vars(criteria)

        alts: list[Alternative] = []
        for a_data in alternatives:
            alt = Alternative(
                id=a_data.get("id", f"alt_{len(alts)+1}"),
                description=a_data.get("description", ""),
                scores=a_data.get("scores", {}),
                rationale=a_data.get("rationale", ""),
            )
            alt.weighted = sum(alt.scores.get(k, 0.5) * w for k, w in crit_dict.items())
            alts.append(alt)

        alts.sort(key=lambda a: a.weighted, reverse=True)
        winner = alts[0]
        margin = winner.weighted - alts[1].weighted if len(alts) > 1 else 0.0

        result = DecisionResult(
            winner=winner,
            alternatives=alts,
            criteria=criteria,
            task_type=task_type,
            margin=margin,
        )
        self._decisions.append(result)
        logger.info(
            f"[DecisionEngine] Qalib: [{winner.id}] skor={winner.weighted:.3f} margin=+{margin:.1%}"
        )
        return result

    def compare_plans(self, plan_a: str, plan_b: str, task_type: str = "simple") -> DecisionResult:
        def score_plan(plan: str) -> dict:
            words = len(plan.split())
            steps = plan.lower().count("addım") + plan.lower().count("step") + plan.count("\n")
            detail = min(1.0, words / 200)
            brevity = max(0.0, 1.0 - words / 500)
            struct = min(1.0, steps / 5)
            return {
                "accuracy": (detail + struct) / 2,
                "latency": brevity,
                "compute": brevity,
                "reliability": min(1.0, struct * 1.2),
                "complexity": brevity,
            }

        alts = [
            {"id": "plan_a", "description": plan_a[:80], "scores": score_plan(plan_a)},
            {"id": "plan_b", "description": plan_b[:80], "scores": score_plan(plan_b)},
        ]
        return self.decide(alts, task_type=task_type)

    def history_summary(self) -> dict:
        if not self._decisions:
            return {"total": 0}
        task_types = [d.task_type for d in self._decisions]
        avg_margin = sum(d.margin for d in self._decisions) / len(self._decisions)
        return {
            "total": len(self._decisions),
            "avg_margin": f"{avg_margin:.1%}",
            "task_types": {t: task_types.count(t) for t in set(task_types)},
        }
