"""
Reflexion Agent – uğursuzluqdan sonra özünü tənqid edib yenidən cəhd edir.

İlham: Shinn et al. 2023 (Reflexion).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from agents.base import BaseAgent, AgentResult
from core.logger import logger


class ReflexionAgent(BaseAgent):
    """Generate → Reflect → Retry döngüsü."""

    MAX_RETRIES = 2

    def __init__(self, name: str = "ReflexionAgent", description: str = "Self-reflective retry agent"):
        super().__init__(name=name, description=description)

    def run(self, task: str, context: Optional[Dict[str, Any]] = None) -> AgentResult:
        context = context or {}
        max_retries = int(context.get("max_retries", self.MAX_RETRIES))
        base_type = context.get("base_agent", "research")

        try:
            from agents.manager import agent_manager
            from brain import ThinkingBrain
        except Exception as e:
            return AgentResult(success=False, error=str(e))

        brain = ThinkingBrain(name="ReflexionBrain", enable_meta=True)
        reflections: List[str] = []
        last_output = None
        last_success = False

        for attempt in range(1, max_retries + 2):
            prompt = task
            if reflections:
                prompt = (
                    f"Tapşırıq: {task}\n\n"
                    f"Əvvəlki cəhdlərin tənqidi:\n" + "\n".join(f"- {r}" for r in reflections)
                    + "\n\nBu tənqidləri nəzərə alaraq daha yaxşı cavab ver."
                )

            # Base agent və ya birbaşa brain
            if base_type in agent_manager.list_types():
                agent = agent_manager.create(base_type, name=f"reflexion_base_{attempt}")
                result = agent_manager.run(agent.id, prompt)
                last_output = result.output
                last_success = result.success
                conf = (result.metadata or {}).get("confidence", 0.6)
            else:
                tr = brain.think(prompt, goal=task, reasoning_mode="tot")
                last_output = tr.get("conclusion")
                last_success = True
                conf = float(tr.get("confidence", 0.5))

            # Reflect
            reflect = brain.think(
                f"Tapşırıq: {task}\n\nCavab: {str(last_output)[:500]}\n\n"
                f"Bu cavab kifayət qədər yaxşıdırmı? Çatışmazlıqları qısa siyahıla. "
                f"Əgər yaxşıdırsa 'OK' yaz.",
                goal="Səmimi özünütənqid",
                reasoning_mode="cot",
                allow_rethink=False,
            )
            critique = str(reflect.get("conclusion") or "")
            reflections.append(critique)

            logger.info(f"Reflexion attempt {attempt}: conf≈{conf}, critique={critique[:80]}")

            # Stop if critique says OK or confidence high
            if "ok" in critique.lower()[:20] or float(reflect.get("confidence", 0)) > 0.85:
                break
            if attempt > max_retries:
                break

        return AgentResult(
            success=last_success,
            output=last_output,
            metadata={
                "method": "reflexion",
                "attempts": len(reflections),
                "reflections": reflections,
            },
        )
