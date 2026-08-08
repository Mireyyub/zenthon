"""
Brain Orchestrator – single path: ReasoningEngine → optional agent → decision.
"""

from __future__ import annotations

import asyncio
from typing import Any, Callable, Dict, Optional, Union

from core.logger import logger
from core.event_bus import event_bus


class Orchestrator:
    """Legacy thin wrapper — prefer BrainOrchestrator."""

    def __init__(self, brain=None):
        self.brain = brain

    def run_cycle(self, input_data: Any) -> Dict[str, Any]:
        orch = BrainOrchestrator()
        return orch.run(str(input_data), use_session=False)


class BrainOrchestrator:
    """Canonical entry: always ReasoningEngine (no parallel think path)."""

    def __init__(self, brain_name: str = "Leon"):
        self.brain_name = brain_name
        self._agent_manager = None
        self._memory_manager = None
        self._knowledge = None
        self._session = None
        self._archival = None
        self._hitl: Optional[Callable[[Dict], bool]] = None
        self._reasoning = None
        logger.info(f"BrainOrchestrator ready ({brain_name}).")

    @property
    def reasoning(self):
        if self._reasoning is None:
            from brain.reasoning.engine import ReasoningEngine

            self._reasoning = ReasoningEngine(persist_traces=True)
        return self._reasoning

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
        allow_experimental_agent: bool = False,
        **_deprecated,
    ) -> Dict[str, Any]:
        """
        Always uses ReasoningEngine.

        Deprecated kwargs (ignored): use_reasoning_engine — always True now.
        """
        query = input_data if isinstance(input_data, str) else str(input_data)

        if use_session:
            self.session.add("user", query)
            sess_ctx = self.session.as_context(8)
            if sess_ctx:
                # session context is appended for archival/LLM enrichment only;
                # curriculum matching still uses bare query in engine via evidence
                pass

        archival_hits = self.archival.search(query, top_k=3)

        rr = self.reasoning.reason(
            query,
            strategy=reasoning_mode,
            goal=goal,
            use_brain=True,
            reasoning_mode=None if reasoning_mode == "auto" else reasoning_mode,
        )

        result: Dict[str, Any] = {
            "conclusion": rr.get("answer"),
            "answer": rr.get("answer"),
            "confidence": rr.get("confidence"),
            "confidence_label": rr.get("confidence_label"),
            "reasoning_mode": rr.get("reasoning_mode"),
            "strategy": rr.get("strategy"),
            "llm_used": rr.get("llm_used"),
            "decision": rr.get("decision"),
            "evidence": rr.get("evidence"),
            "trace_id": rr.get("trace_id"),
            "trace": rr.get("trace"),
            "source": rr.get("source"),
            "validation": rr.get("validation"),
            "conflict": rr.get("conflict"),
            "name": self.brain_name,
            "archival_hits": archival_hits,
        }

        if agent_type and self.agents:
            try:
                agent = self.agents.create(
                    agent_type, allow_experimental=allow_experimental_agent
                )
                task = result.get("conclusion") or query
                agent_result = self.agents.run(
                    agent.id, str(task), context=agent_context or {}
                )
                result["agent"] = {
                    "type": agent_type,
                    "success": agent_result.success,
                    "output": agent_result.output,
                    "metadata": agent_result.metadata,
                    "error": agent_result.error,
                }
                if agent_result.success and agent_result.output is not None:
                    result["agent_output"] = agent_result.output
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
                return result

        if use_session and result.get("conclusion"):
            self.session.add("assistant", str(result["conclusion"])[:1000])

        if archive_result and result.get("conclusion"):
            self.archival.store(
                str(result["conclusion"])[:800],
                tags=[result.get("reasoning_mode", "think")],
                importance=float(result.get("confidence", 0.5)),
            )

        if self.memory and result.get("conclusion") and result.get("conclusion") != "UNKNOWN":
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
                "mode": result.get("reasoning_mode"),
                "confidence": result.get("confidence"),
                "source": result.get("source"),
                "trace_id": result.get("trace_id"),
                "agent": agent_type,
                "name": self.brain_name,
            },
            source="orchestrator",
        )
        return result

    async def arun(self, *args, **kwargs) -> Dict[str, Any]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: self.run(*args, **kwargs))

    def status(self) -> Dict[str, Any]:
        types = []
        if self.agents:
            try:
                types = self.agents.list_types_detailed()
            except Exception:
                types = self.agents.list_types()
        return {
            "brain_name": self.brain_name,
            "reasoning": "ReasoningEngine",
            "agents": types,
            "memory_stats": self.memory.stats() if self.memory else {},
            "session_turns": len(self.session.turns),
            "archival_count": self.archival.count(),
            "knowledge": self.knowledge.graph.stats()
            if self.knowledge and hasattr(self.knowledge, "graph")
            else {},
        }
