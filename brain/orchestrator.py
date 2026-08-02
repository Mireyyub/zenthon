"""
Brain Orchestrator – ThinkingBrain, Memory, Knowledge və Agent-ləri əlaqələndirir.

Mövcud core.Brain ilə geriyə uyğun qalır, əlavə olaraq tam kognitiv dövrə təqdim edir.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from core.logger import logger
from core.event_bus import event_bus
from brain.core import Brain


class Orchestrator:
    """Minimal (köhnə) orchestrator – geriyə uyğunluq."""

    def __init__(self, brain: Brain):
        self.brain = brain

    def run_cycle(self, input_data: Any) -> Dict[str, Any]:
        return self.brain.think(input_data)


class BrainOrchestrator:
    """
    Tam kognitiv orchestrator.

    Axın:
      input → ThinkingBrain.think
            → (opsional) Agent icrası
            → Memory/Knowledge yeniləmə
            → Event publish
    """

    def __init__(self, brain_name: str = "ZenthonBrain"):
        from brain.core_brain import ThinkingBrain

        self.brain = ThinkingBrain(name=brain_name, enable_meta=True)
        self._agent_manager = None
        self._memory_manager = None
        self._knowledge = None
        logger.info("BrainOrchestrator ready.")

    @property
    def agents(self):
        if self._agent_manager is None:
            try:
                from agents.manager import agent_manager
                self._agent_manager = agent_manager
            except Exception:
                self._agent_manager = None
        return self._agent_manager

    @property
    def memory(self):
        if self._memory_manager is None:
            try:
                from memory import MemoryManager
                self._memory_manager = MemoryManager()
            except Exception:
                self._memory_manager = None
        return self._memory_manager

    @property
    def knowledge(self):
        if self._knowledge is None:
            try:
                from knowledge import KnowledgeRetrieval
                self._knowledge = KnowledgeRetrieval()
            except Exception:
                self._knowledge = None
        return self._knowledge

    def run(
        self,
        input_data: Union[str, Dict[str, Any]],
        goal: Optional[str] = None,
        reasoning_mode: str = "auto",
        agent_type: Optional[str] = None,
        agent_context: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Tam dövrə: think → optional agent → persist.
        """
        # 1. Think
        result = self.brain.think(
            input_data,
            goal=goal,
            reasoning_mode=reasoning_mode,
            use_knowledge=True,
        )

        # 2. Optional specialized agent
        agent_result = None
        if agent_type and self.agents:
            try:
                agent = self.agents.create(agent_type)
                task = result.get("conclusion") or str(input_data)
                agent_result = self.agents.run(
                    agent.id, task, context=agent_context or {}
                )
                result["agent"] = {
                    "type": agent_type,
                    "success": agent_result.success,
                    "output": agent_result.output,
                    "metadata": agent_result.metadata,
                }
            except Exception as e:
                logger.warning(f"Agent '{agent_type}' failed: {e}")
                result["agent"] = {"type": agent_type, "success": False, "error": str(e)}

        # 3. Persist key conclusion into platform memory
        if self.memory and result.get("conclusion"):
            try:
                self.memory.remember(
                    str(result["conclusion"])[:500],
                    kind="vector",
                    metadata={"cycle": result.get("cycle"), "mode": result.get("reasoning_mode")},
                )
            except Exception:
                pass

        if self.knowledge and result.get("conclusion"):
            try:
                self.knowledge.facts.add(
                    str(result["conclusion"])[:300],
                    source="brain_orchestrator",
                    confidence=float(result.get("confidence", 0.5)),
                )
            except Exception:
                pass

        event_bus.publish(
            "OrchestratorCycleDone",
            {
                "cycle": result.get("cycle"),
                "mode": result.get("reasoning_mode"),
                "confidence": result.get("confidence"),
                "agent": agent_type,
            },
            source="orchestrator",
        )
        return result

    def status(self) -> Dict[str, Any]:
        return {
            "brain": self.brain.get_state(),
            "agents_available": self.agents.list_types() if self.agents else [],
            "memory_stats": self.memory.stats() if self.memory else {},
            "knowledge": self.knowledge.graph.stats() if self.knowledge else {},
        }
