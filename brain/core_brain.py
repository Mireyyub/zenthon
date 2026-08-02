"""
Core Thinking Brain for Zenthon Multimodal AI System.

Perception → Memory → Reasoning → Action dövrünü idarə edən kognitiv nüvə.
"""

from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
import uuid

from core.logger import logger


@dataclass
class Thought:
    """Tək bir düşüncə vahidi."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    content: str = ""
    modality: str = "text"
    confidence: float = 1.0
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BrainState:
    """Beynin cari vəziyyəti."""
    working_memory: List[Thought] = field(default_factory=list)
    current_goal: Optional[str] = None
    active_plan: List[str] = field(default_factory=list)
    last_reasoning_trace: List[str] = field(default_factory=list)
    cycle_count: int = 0
    last_decision: Optional[Dict[str, Any]] = None


class ThinkingBrain:
    """
    Zenthon-un əsas düşünən beyni.

    Multimodal AI tətbiqləri üçün kognitiv nüvə.
    """

    MAX_WORKING_MEMORY = 30

    def __init__(self, name: str = "ZenthonBrain"):
        self.name = name
        self.state = BrainState()
        self._perception = None
        self._memory = None
        self._reasoning = None
        self._action = None
        logger.info(f"ThinkingBrain '{self.name}' initialized.")

    # ------------------------------------------------------------------
    # Lazy-loaded submodules
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # Əsas düşünmə dövrü
    # ------------------------------------------------------------------
    def think(
        self,
        input_data: Union[str, Dict[str, Any], List[Any]],
        goal: Optional[str] = None,
        reasoning_mode: str = "auto",
        max_steps: int = 8,
    ) -> Dict[str, Any]:
        """
        Əsas düşünmə funksiyası.

        Args:
            input_data: Mətn, dict (multimodal) və ya list.
            goal: Məqsəd (opsional).
            reasoning_mode: "cot" | "tot" | "sot" | "auto"
            max_steps: Maksimum düşünmə addımı.

        Returns:
            Nəticə lüğəti (conclusion, trace, decision, confidence və s.).
        """
        self.state.cycle_count += 1
        if goal:
            self.state.current_goal = goal

        logger.info(
            f"[Brain Cycle {self.state.cycle_count}] Thinking started | mode={reasoning_mode}"
        )

        # 1. Perception
        perceived = self.perception.process(input_data)
        thought = Thought(
            content=str(perceived.get("summary", perceived)),
            modality=perceived.get("modality", "text"),
            confidence=float(perceived.get("confidence", 0.9)),
            metadata=perceived,
        )

        # İş yaddaşı limiti
        self.state.working_memory.append(thought)
        if len(self.state.working_memory) > self.MAX_WORKING_MEMORY:
            self.state.working_memory = self.state.working_memory[-self.MAX_WORKING_MEMORY :]

        # 2. Memory retrieval
        relevant = self._retrieve_relevant_memories(thought)

        # 3. Reasoning mode seçimi
        selected_mode = self._select_mode(reasoning_mode, thought, goal)
        reasoner = self.reasoning.get(selected_mode, self.reasoning["cot"])

        reasoning_result = reasoner.reason(
            query=thought.content,
            context=relevant,
            goal=self.state.current_goal,
            max_steps=max_steps,
        )
        self.state.last_reasoning_trace = reasoning_result.get("trace", [])

        # 4. Yaddaşa yaz
        self.memory["short_term"].add(thought)
        self.memory["episodic"].store_episode(
            event=thought.content,
            reasoning_trace=self.state.last_reasoning_trace,
            outcome=reasoning_result.get("conclusion"),
        )

        # 5. Qərar
        decision = self.action.decide(
            reasoning_result=reasoning_result,
            goal=self.state.current_goal,
            working_memory=self.state.working_memory,
        )
        self.state.last_decision = decision

        result = {
            "cycle": self.state.cycle_count,
            "input_summary": thought.content,
            "modality": thought.modality,
            "reasoning_mode": selected_mode,
            "trace": self.state.last_reasoning_trace,
            "conclusion": reasoning_result.get("conclusion"),
            "decision": decision,
            "confidence": float(reasoning_result.get("confidence", 0.0)),
            "memories_used": len(relevant),
        }

        logger.info(
            f"[Brain Cycle {self.state.cycle_count}] Finished | "
            f"mode={selected_mode} | confidence={result['confidence']:.3f} | "
            f"action={decision.get('action')}"
        )
        return result

    def _select_mode(self, mode: str, thought: Thought, goal: Optional[str]) -> str:
        """Auto rejimində ən uyğun reasoning strategiyasını seç."""
        mode = (mode or "auto").lower().strip()
        if mode in ("cot", "tot", "sot"):
            return mode

        # Auto seçim məntiqi
        text = thought.content.lower()
        word_count = len(text.split())

        # Uzun / struktur tələb edən suallar → Skeleton-of-Thought
        if word_count > 40 or any(
            k in text for k in ("plan", "addım", "struktur", "mərhələ", "necə qur", "architect")
        ):
            return "sot"

        # Müqayisə / alternativ / yaradıcı → Tree-of-Thoughts
        if any(
            k in text
            for k in (
                "müqayisə",
                "alternativ",
                "yaxşı",
                "pis",
                "seç",
                "hansı",
                "yaradıcı",
                "vs",
                "yoxsa",
            )
        ):
            return "tot"

        # Sadə və birbaşa suallar → Chain-of-Thought
        return "cot"

    def _retrieve_relevant_memories(self, thought: Thought, top_k: int = 5) -> List[str]:
        short = self.memory["short_term"].retrieve(top_k=top_k)
        long_ = self.memory["long_term"].retrieve(query=thought.content, top_k=top_k)
        episodic = self.memory["episodic"].retrieve(query=thought.content, top_k=3)
        return short + long_ + episodic

    # ------------------------------------------------------------------
    # Köməkçi metodlar
    # ------------------------------------------------------------------
    def set_goal(self, goal: str) -> List[str]:
        """Yeni məqsəd təyin et və plan yarat."""
        self.state.current_goal = goal
        plan = self.reasoning["planner"].create_plan(goal)
        self.state.active_plan = plan
        logger.info(f"New goal set: {goal}")
        return plan

    def remember(self, key: str, value: Any, metadata: Optional[Dict] = None) -> str:
        """Uzunmüddətli yaddaşa məlumat yaz."""
        return self.memory["long_term"].store(key, value, metadata)

    def recall(self, query: str, top_k: int = 5) -> List[str]:
        """Uzunmüddətli yaddaşdan axtar."""
        return self.memory["long_term"].retrieve(query, top_k=top_k)

    def get_state(self) -> Dict[str, Any]:
        """Cari beyin vəziyyətini qaytar."""
        return {
            "name": self.name,
            "cycle_count": self.state.cycle_count,
            "current_goal": self.state.current_goal,
            "working_memory_size": len(self.state.working_memory),
            "active_plan": self.state.active_plan,
            "last_trace": self.state.last_reasoning_trace[-5:]
            if self.state.last_reasoning_trace
            else [],
            "last_decision": self.state.last_decision,
        }

    def reset(self, clear_long_term: bool = False) -> None:
        """İş yaddaşı və vəziyyəti sıfırla."""
        self.state = BrainState()
        self.memory["short_term"].clear()
        self.memory["episodic"].clear()
        if clear_long_term:
            self.memory["long_term"].clear()
        logger.info("ThinkingBrain state reset.")

    def __repr__(self) -> str:
        return (
            f"ThinkingBrain(name={self.name!r}, cycles={self.state.cycle_count}, "
            f"goal={self.state.current_goal!r})"
        )
