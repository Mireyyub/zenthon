"""
Brain Orchestrator (Leon) – think + agents + memory + HITL + checkpoints + async.
"""

from __future__ import annotations

import asyncio
from typing import Any, Callable, Dict, Optional, Union

from core.logger import logger
from core.event_bus import event_bus
from brain.core import Brain


class Orchestrator:
    def __init__(self, brain: Brain):
        self.brain = brain

    def run_cycle(self, input_data: Any) -> Dict[str, Any]:
        return self.brain.think(input_data)


class BrainOrchestrator:
    def __init__(self, brain_name: str = "Leon"):
        from brain.core_brain import ThinkingBrain

        self.brain = ThinkingBrain(name=brain_name, enable_meta=True)
        self._agent_manager = None
        self._memory_manager = None
        self._knowledge = None
        self._session = None
        self._archival = None
        self._hitl: Optional[Callable[[Dict], bool]] = None
        logger.info(f"BrainOrchestrator ready ({brain_name}).")

    def set_hitl(self, callback: Callable[[Dict], bool]) -> None:
        self._hitl = callback

    @property
    def session(self):
        if self._session is None:
            from memory.session import SessionMemory
            self._session = SessionMemory()
        return self._session

    @property
    def archival(self):
        if self._archival is None:
            from memory.archival import ArchivalMemory
            self._archival = ArchivalMemory()
        return self._archival

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
        use_session: bool = True,
        archive_result: bool = False,
        checkpoint_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        query = input_data if isinstance(input_data, str) else str(input_data)
        if use_session:
            self.session.add("user", query)
            sess_ctx = self.session.as_context(8)
            query_for_brain = (
                f"Söhbət konteksti:\n{sess_ctx}\n\nCari sual: {query}" if sess_ctx else query
            )
        else:
            query_for_brain = query

        archival_hits = self.archival.search(query, top_k=3)
        if archival_hits:
            query_for_brain += "\n\nArxiv xatirələr:\n" + "\n".join(f"- {h}" for h in archival_hits)

        result = self.brain.think(
            query_for_brain,
            goal=goal,
            reasoning_mode=reasoning_mode,
            use_knowledge=True,
        )

        if agent_type and self.agents:
            try:
                agent = self.agents.create(agent_type)
                task = result.get("conclusion") or query
                agent_result = self.agents.run(agent.id, task, context=agent_context or {})
                result["agent"] = {
                    "type": agent_type,
                    "success": agent_result.success,
                    "output": agent_result.output,
                    "metadata": agent_result.metadata,
                }
            except Exception as e:
                result["agent"] = {"type": agent_type, "success": False, "error": str(e)}

        if self._hitl:
            accepted = self._hitl(result)
            result["hitl_accepted"] = bool(accepted)
            if not accepted:
                result["decision"] = {
                    **(result.get("decision") or {}),
                    "action": "rejected_by_human",
                    "message": "Human-in-the-loop rədd etdi",
                }
                event_bus.publish("HITLRejected", {"cycle": result.get("cycle")}, source="orchestrator")
                return result

        if use_session and result.get("conclusion"):
            self.session.add("assistant", str(result["conclusion"])[:1000])

        if archive_result and result.get("conclusion"):
            self.archival.store(
                str(result["conclusion"])[:800],
                tags=[result.get("reasoning_mode", "think")],
                importance=float(result.get("confidence", 0.5)),
            )

        if self.memory and result.get("conclusion"):
            try:
                self.memory.remember(str(result["conclusion"])[:500], kind="vector")
            except Exception:
                pass

        if checkpoint_name:
            try:
                from core.checkpoint import checkpoint_store

                cp_id = checkpoint_store.save(
                    checkpoint_name,
                    {"result": result, "session": self.session.history(20), "goal": goal},
                )
                result["checkpoint_id"] = cp_id
            except Exception as e:
                logger.warning(f"Checkpoint failed: {e}")

        event_bus.publish(
            "OrchestratorCycleDone",
            {
                "cycle": result.get("cycle"),
                "mode": result.get("reasoning_mode"),
                "confidence": result.get("confidence"),
                "agent": agent_type,
                "name": getattr(self.brain, "name", "Leon"),
            },
            source="orchestrator",
        )
        return result

    async def arun(self, *args, **kwargs) -> Dict[str, Any]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: self.run(*args, **kwargs))

    def status(self) -> Dict[str, Any]:
        return {
            "brain": self.brain.get_state(),
            "agents_available": self.agents.list_types() if self.agents else [],
            "memory_stats": self.memory.stats() if self.memory else {},
            "session_turns": len(self.session.turns),
            "archival_count": self.archival.count(),
            "knowledge": self.knowledge.graph.stats() if self.knowledge else {},
        }
