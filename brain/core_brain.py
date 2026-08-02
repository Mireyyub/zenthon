"""
Core Thinking Brain – kognitiv nüvə + async API.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
import uuid
import asyncio

from core.logger import logger
from core.event_bus import event_bus


@dataclass
class Thought:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    content: str = ""
    modality: str = "text"
    confidence: float = 1.0
    importance: float = 0.5
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    source: str = "perception"


@dataclass
class BrainState:
    working_memory: List[Thought] = field(default_factory=list)
    current_goal: Optional[str] = None
    active_plan: List[str] = field(default_factory=list)
    last_reasoning_trace: List[str] = field(default_factory=list)
    cycle_count: int = 0
    last_decision: Optional[Dict[str, Any]] = None
    uncertainty: float = 0.0
    reflection_log: List[str] = field(default_factory=list)


class ThinkingBrain:
    MAX_WORKING_MEMORY = 40
    LOW_CONFIDENCE_THRESHOLD = 0.62

    def __init__(self, name: str = "ZenthonBrain", enable_meta: bool = True):
        self.name = name
        self.enable_meta = enable_meta
        self.state = BrainState()
        self._perception = None
        self._memory = None
        self._memory_manager = None
        self._knowledge = None
        self._graphrag = None
        self._reasoning = None
        self._action = None
        self._reflection = None
        self._goals = None
        logger.info(f"ThinkingBrain '{self.name}' initialized (meta={enable_meta}).")

    @property
    def perception(self):
        if self._perception is None:
            from brain.perception.multimodal_fusion import MultimodalPerception
            self._perception = MultimodalPerception()
        return self._perception

    @property
    def memory(self):
        if self._memory is None:
            from brain.memory.short_term import ShortTermMemory
            from brain.memory.long_term import LongTermMemory
            from brain.memory.episodic import EpisodicMemory
            self._memory = {
                "short_term": ShortTermMemory(capacity=self.MAX_WORKING_MEMORY),
                "long_term": LongTermMemory(),
                "episodic": EpisodicMemory(),
            }
        return self._memory

    @property
    def memory_manager(self):
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

    @property
    def graphrag(self):
        if self._graphrag is None:
            try:
                from knowledge.graphrag import GraphRAG
                self._graphrag = GraphRAG()
            except Exception:
                self._graphrag = None
        return self._graphrag

    @property
    def reasoning(self):
        if self._reasoning is None:
            from brain.reasoning.chain_of_thought import ChainOfThought
            from brain.reasoning.tree_of_thoughts import TreeOfThoughts
            from brain.reasoning.skeleton_of_thought import SkeletonOfThought
            from brain.reasoning.planner import Planner
            self._reasoning = {
                "cot": ChainOfThought(),
                "tot": TreeOfThoughts(),
                "sot": SkeletonOfThought(),
                "planner": Planner(),
            }
        return self._reasoning

    @property
    def action(self):
        if self._action is None:
            from brain.action.decision import DecisionEngine
            self._action = DecisionEngine()
        return self._action

    @property
    def reflection_engine(self):
        if self._reflection is None:
            from brain.reflection import ReflectionEngine
            self._reflection = ReflectionEngine()
        return self._reflection

    @property
    def goals(self):
        if self._goals is None:
            from brain.goals import GoalManager
            self._goals = GoalManager()
        return self._goals

    def think(
        self,
        input_data: Union[str, Dict[str, Any], List[Any]],
        goal: Optional[str] = None,
        reasoning_mode: str = "auto",
        max_steps: int = 8,
        allow_rethink: bool = True,
        use_knowledge: bool = True,
    ) -> Dict[str, Any]:
        self.state.cycle_count += 1
        if goal:
            self.state.current_goal = goal
            if not self.goals.get_active():
                self.goals.create(goal)

        logger.info(f"[Brain Cycle {self.state.cycle_count}] START | mode={reasoning_mode}")

        perceived = self.perception.process(input_data)
        thought = Thought(
            content=str(perceived.get("summary", perceived)),
            modality=perceived.get("modality", "text"),
            confidence=float(perceived.get("confidence", 0.9)),
            importance=self._estimate_importance(perceived),
            metadata=perceived,
            source="perception",
        )
        self._add_to_working_memory(thought)
        relevant = self._retrieve_full_context(thought, use_knowledge=use_knowledge)

        selected_mode = self._select_mode(reasoning_mode, thought, goal)
        reasoner = self.reasoning.get(selected_mode, self.reasoning["cot"])
        reasoning_result = reasoner.reason(
            query=thought.content,
            context=relevant,
            goal=self.state.current_goal,
            max_steps=max_steps,
        )
        self.state.last_reasoning_trace = reasoning_result.get("trace", [])

        if self.enable_meta:
            report = self.reflection_engine.reflect(
                reasoning_result,
                context_size=len(relevant),
                cycle=self.state.cycle_count,
                goal=self.state.current_goal,
            )
            reasoning_result = self.reflection_engine.apply(reasoning_result, report)
            self.state.reflection_log.append(
                f"[{report.quality}] {', '.join(report.issues) or 'ok'}"
            )

        confidence = float(reasoning_result.get("confidence", 0.0))
        used_modes = [selected_mode]

        if allow_rethink and confidence < self.LOW_CONFIDENCE_THRESHOLD:
            alt_mode = self._pick_alternative_mode(selected_mode)
            alt_result = self.reasoning[alt_mode].reason(
                query=thought.content,
                context=relevant,
                goal=self.state.current_goal,
                max_steps=max_steps,
            )
            if self.enable_meta:
                alt_report = self.reflection_engine.reflect(
                    alt_result, len(relevant), self.state.cycle_count, self.state.current_goal
                )
                alt_result = self.reflection_engine.apply(alt_result, alt_report)
            if float(alt_result.get("confidence", 0)) > confidence:
                reasoning_result = alt_result
                selected_mode = alt_mode
                confidence = float(alt_result.get("confidence", 0))
                self.state.last_reasoning_trace = alt_result.get("trace", [])
            used_modes.append(alt_mode)

        self.state.uncertainty = 1.0 - confidence

        self.memory["short_term"].add(thought)
        self.memory["episodic"].store_episode(
            event=thought.content,
            reasoning_trace=self.state.last_reasoning_trace,
            outcome=reasoning_result.get("conclusion"),
            metadata={"confidence": confidence, "mode": selected_mode, "importance": thought.importance},
        )
        if self.memory_manager:
            try:
                self.memory_manager.remember(
                    thought.content, kind="vector",
                    metadata={"cycle": self.state.cycle_count, "mode": selected_mode},
                )
            except Exception:
                pass

        decision = self.action.decide(
            reasoning_result=reasoning_result,
            goal=self.state.current_goal,
            working_memory=self.state.working_memory,
            uncertainty=self.state.uncertainty,
        )
        self.state.last_decision = decision

        event_bus.publish(
            "BrainCycleCompleted",
            {"cycle": self.state.cycle_count, "mode": selected_mode, "confidence": confidence},
            source="brain",
        )

        # Async bus best-effort
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                from core.async_event_bus import async_event_bus
                asyncio.create_task(
                    async_event_bus.publish(
                        "BrainCycleCompleted",
                        {"cycle": self.state.cycle_count, "mode": selected_mode, "confidence": confidence},
                        source="brain",
                    )
                )
        except Exception:
            pass

        result = {
            "cycle": self.state.cycle_count,
            "input_summary": thought.content,
            "modality": thought.modality,
            "reasoning_mode": selected_mode,
            "modes_tried": used_modes,
            "trace": self.state.last_reasoning_trace,
            "conclusion": reasoning_result.get("conclusion"),
            "decision": decision,
            "confidence": round(confidence, 3),
            "uncertainty": round(self.state.uncertainty, 3),
            "memories_used": len(relevant),
            "reflection": reasoning_result.get("reflection"),
            "llm_used": reasoning_result.get("llm_used", False),
        }
        logger.info(
            f"[Brain Cycle {self.state.cycle_count}] END | mode={selected_mode} | conf={confidence:.3f}"
        )
        return result

    async def athink(
        self,
        input_data: Union[str, Dict[str, Any], List[Any]],
        goal: Optional[str] = None,
        reasoning_mode: str = "auto",
        max_steps: int = 8,
        allow_rethink: bool = True,
        use_knowledge: bool = True,
    ) -> Dict[str, Any]:
        """Async think – event loop-u bloklamır."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.think(
                input_data,
                goal=goal,
                reasoning_mode=reasoning_mode,
                max_steps=max_steps,
                allow_rethink=allow_rethink,
                use_knowledge=use_knowledge,
            ),
        )

    def _retrieve_full_context(self, thought: Thought, use_knowledge: bool = True) -> List[str]:
        ctx: List[str] = []
        ctx += self.memory["short_term"].retrieve(top_k=4)
        ctx += self.memory["long_term"].retrieve(query=thought.content, top_k=3)
        ctx += self.memory["episodic"].retrieve(query=thought.content, top_k=2)
        if self.memory_manager:
            try:
                recalled = self.memory_manager.recall(thought.content, top_k=3)
                for text, score in recalled.get("vector", [])[:3]:
                    ctx.append(text)
                for fact in recalled.get("semantic", [])[:2]:
                    if isinstance(fact, dict):
                        ctx.append(
                            f"{fact.get('subject')} {fact.get('predicate')} {fact.get('object')}"
                        )
            except Exception:
                pass
        if use_knowledge and self.knowledge:
            try:
                kr = self.knowledge.retrieve(thought.content, top_k=3)
                for f in kr.get("facts", [])[:3]:
                    ctx.append(f["statement"] if isinstance(f, dict) else str(f))
                for n in kr.get("nodes", [])[:2]:
                    ctx.append(n.get("label", str(n)))
            except Exception:
                pass
        if use_knowledge and self.graphrag:
            try:
                gr = self.graphrag.retrieve(thought.content, top_k=4)
                ctx.extend(gr.get("combined", [])[:4])
            except Exception:
                pass
        seen = set()
        unique = []
        for c in ctx:
            key = str(c)[:100]
            if key not in seen:
                seen.add(key)
                unique.append(str(c))
        return unique[:14]

    def _add_to_working_memory(self, thought: Thought) -> None:
        self.state.working_memory.append(thought)
        if len(self.state.working_memory) > self.MAX_WORKING_MEMORY:
            scored = [
                (i, t.importance * 0.6 + (i / len(self.state.working_memory)) * 0.4)
                for i, t in enumerate(self.state.working_memory)
            ]
            scored.sort(key=lambda x: x[1])
            self.state.working_memory.pop(scored[0][0])

    def _estimate_importance(self, perceived: Dict[str, Any]) -> float:
        conf = float(perceived.get("confidence", 0.5))
        modality = perceived.get("modality", "text")
        boost = 0.1 if modality == "multimodal" else 0.0
        length = len(str(perceived.get("summary", "")))
        return round(min(1.0, conf * 0.7 + boost + min(0.2, length / 500)), 3)

    def _select_mode(self, mode: str, thought: Thought, goal: Optional[str]) -> str:
        mode = (mode or "auto").lower().strip()
        if mode in ("cot", "tot", "sot"):
            return mode
        text = thought.content.lower()
        wc = len(text.split())
        if wc > 35 or any(k in text for k in ("plan", "addım", "struktur", "mərhələ", "architect", "roadmap")):
            return "sot"
        if any(k in text for k in ("müqayisə", "alternativ", "seç", "hansı", "vs", "yoxsa", "fərq", "üstünlük")):
            return "tot"
        return "cot"

    def _pick_alternative_mode(self, current: str) -> str:
        return {"cot": "tot", "tot": "sot", "sot": "cot"}.get(current, "tot")

    def set_goal(self, goal: str) -> List[str]:
        self.state.current_goal = goal
        plan = self.reasoning["planner"].create_plan(goal)
        self.state.active_plan = plan
        self.goals.create(goal, plan=plan)
        return plan

    def remember(self, key: str, value: Any, metadata: Optional[Dict] = None) -> str:
        mid = self.memory["long_term"].store(key, value, metadata)
        if self.memory_manager:
            try:
                self.memory_manager.remember(str(value), kind="vector", metadata=metadata)
            except Exception:
                pass
        return mid

    def recall(self, query: str, top_k: int = 5) -> List[str]:
        return self.memory["long_term"].retrieve(query, top_k=top_k)

    def get_state(self) -> Dict[str, Any]:
        active = self.goals.get_active()
        return {
            "name": self.name,
            "cycle_count": self.state.cycle_count,
            "current_goal": self.state.current_goal,
            "active_goal_id": active.id if active else None,
            "working_memory_size": len(self.state.working_memory),
            "active_plan": self.state.active_plan,
            "last_trace": self.state.last_reasoning_trace[-6:] if self.state.last_reasoning_trace else [],
            "last_decision": self.state.last_decision,
            "uncertainty": self.state.uncertainty,
            "recent_reflections": self.state.reflection_log[-3:],
        }

    def reset(self, clear_long_term: bool = False) -> None:
        self.state = BrainState()
        self.memory["short_term"].clear()
        self.memory["episodic"].clear()
        if clear_long_term:
            self.memory["long_term"].clear()

    def __repr__(self) -> str:
        return (
            f"ThinkingBrain(name={self.name!r}, cycles={self.state.cycle_count}, "
            f"goal={self.state.current_goal!r}, unc={self.state.uncertainty:.2f})"
        )
