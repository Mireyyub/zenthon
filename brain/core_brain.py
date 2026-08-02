"""Core Thinking Brain for Zenthon"""

from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
import uuid

from core.logger import logger


@dataclass
class Thought:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    content: str = ""
    modality: str = "text"
    confidence: float = 1.0
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BrainState:
    working_memory: List[Thought] = field(default_factory=list)
    current_goal: Optional[str] = None
    active_plan: List[str] = field(default_factory=list)
    last_reasoning_trace: List[str] = field(default_factory=list)
    cycle_count: int = 0


class ThinkingBrain:
    def __init__(self, name: str = "ZenthonBrain"):
        self.name = name
        self.state = BrainState()
        self._perception = None
        self._memory = None
        self._reasoning = None
        self._action = None
        logger.info(f"ThinkingBrain '{self.name}' initialized.")

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
                "short_term": ShortTermMemory(),
                "long_term": LongTermMemory(),
                "episodic": EpisodicMemory(),
            }
        return self._memory

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

    def think(self, input_data: Union[str, Dict[str, Any], List[Any]],
              goal: Optional[str] = None, reasoning_mode: str = "cot",
              max_steps: int = 8) -> Dict[str, Any]:
        self.state.cycle_count += 1
        self.state.current_goal = goal
        logger.info(f"[Brain Cycle {self.state.cycle_count}] Thinking started. Mode={reasoning_mode}")

        perceived = self.perception.process(input_data)
        thought = Thought(
            content=str(perceived.get("summary", perceived)),
            modality=perceived.get("modality", "text"),
            confidence=perceived.get("confidence", 0.9),
            metadata=perceived,
        )
        self.state.working_memory.append(thought)

        relevant = self._retrieve_relevant_memories(thought)
        reasoner = self._select_reasoner(reasoning_mode)
        reasoning_result = reasoner.reason(
            query=thought.content, context=relevant, goal=goal, max_steps=max_steps
        )
        self.state.last_reasoning_trace = reasoning_result.get("trace", [])

        self.memory["short_term"].add(thought)
        self.memory["episodic"].store_episode(
            event=thought.content,
            reasoning_trace=self.state.last_reasoning_trace,
            outcome=reasoning_result.get("conclusion"),
        )

        decision = self.action.decide(
            reasoning_result=reasoning_result, goal=goal,
            working_memory=self.state.working_memory,
        )

        result = {
            "cycle": self.state.cycle_count,
            "input_summary": thought.content,
            "modality": thought.modality,
            "reasoning_mode": reasoning_mode,
            "trace": self.state.last_reasoning_trace,
            "conclusion": reasoning_result.get("conclusion"),
            "decision": decision,
            "confidence": reasoning_result.get("confidence", 0.0),
        }
        logger.info(f"[Brain Cycle {self.state.cycle_count}] Finished. Confidence={result['confidence']:.3f}")
        return result

    def _retrieve_relevant_memories(self, thought: Thought, top_k: int = 5) -> List[str]:
        short = self.memory["short_term"].retrieve(top_k=top_k)
        long_ = self.memory["long_term"].retrieve(query=thought.content, top_k=top_k)
        episodic = self.memory["episodic"].retrieve(query=thought.content, top_k=3)
        return short + long_ + episodic

    def _select_reasoner(self, mode: str):
        mode = mode.lower()
        if mode == "auto":
            return self.reasoning["cot"]
        return self.reasoning.get(mode, self.reasoning["cot"])

    def set_goal(self, goal: str) -> None:
        self.state.current_goal = goal
        self.state.active_plan = self.reasoning["planner"].create_plan(goal)
        logger.info(f"New goal set: {goal}")

    def get_state(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "cycle_count": self.state.cycle_count,
            "current_goal": self.state.current_goal,
            "working_memory_size": len(self.state.working_memory),
            "active_plan": self.state.active_plan,
            "last_trace": self.state.last_reasoning_trace[-5:] if self.state.last_reasoning_trace else [],
        }

    def reset(self) -> None:
        self.state = BrainState()
        self.memory["short_term"].clear()
        logger.info("ThinkingBrain state reset.")
