"""
Core Thinking Brain for Zenthon Multimodal AI System.

Gücləndirilmiş kognitiv nüvə:
- Perception → Memory → Reasoning → Meta-Reflection → Decision
- Multi-cycle thinking
- Uncertainty handling
- Working memory with attention
"""

from typing import Any, Dict, List, Optional, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import uuid
import math

from core.logger import logger


@dataclass
class Thought:
    """Tək bir düşüncə vahidi."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    content: str = ""
    modality: str = "text"
    confidence: float = 1.0
    importance: float = 0.5
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    source: str = "perception"  # perception | reasoning | reflection | memory


@dataclass
class BrainState:
    """Beynin cari vəziyyəti."""
    working_memory: List[Thought] = field(default_factory=list)
    current_goal: Optional[str] = None
    active_plan: List[str] = field(default_factory=list)
    last_reasoning_trace: List[str] = field(default_factory=list)
    cycle_count: int = 0
    last_decision: Optional[Dict[str, Any]] = None
    uncertainty: float = 0.0
    reflection_log: List[str] = field(default_factory=list)


class ThinkingBrain:
    """
    Zenthon-un gücləndirilmiş düşünən beyni.

    Xüsusiyyətlər:
    - Avtomatik reasoning mode seçimi
    - Multi-cycle thinking (aşağı etimadda avtomatik ikinci dövrə)
    - Meta-reflection (öz düşüncəsinə baxış)
    - Working memory + attention
    - Uncertainty tracking
    """

    MAX_WORKING_MEMORY = 40
    LOW_CONFIDENCE_THRESHOLD = 0.62
    HIGH_CONFIDENCE_THRESHOLD = 0.82

    def __init__(self, name: str = "ZenthonBrain", enable_meta: bool = True):
        self.name = name
        self.enable_meta = enable_meta
        self.state = BrainState()
        self._perception = None
        self._memory = None
        self._reasoning = None
        self._action = None
        logger.info(f"ThinkingBrain '{self.name}' initialized (meta={enable_meta}).")

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
        allow_rethink: bool = True,
    ) -> Dict[str, Any]:
        """
        Gücləndirilmiş düşünmə funksiyası.

        Aşağı etimadda avtomatik olaraq fərqli mode ilə ikinci dövrə işlədir.
        """
        self.state.cycle_count += 1
        if goal:
            self.state.current_goal = goal

        logger.info(
            f"[Brain Cycle {self.state.cycle_count}] START | mode={reasoning_mode}"
        )

        # 1. Perception
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

        # 2. Memory retrieval (attention-weighted)
        relevant = self._retrieve_with_attention(thought)

        # 3. Reasoning
        selected_mode = self._select_mode(reasoning_mode, thought, goal)
        reasoner = self.reasoning.get(selected_mode, self.reasoning["cot"])

        reasoning_result = reasoner.reason(
            query=thought.content,
            context=relevant,
            goal=self.state.current_goal,
            max_steps=max_steps,
        )
        self.state.last_reasoning_trace = reasoning_result.get("trace", [])

        # 4. Meta-reflection (öz düşüncəsinə baxış)
        if self.enable_meta:
            reflection = self._meta_reflect(reasoning_result, thought, relevant)
            reasoning_result = self._apply_reflection(reasoning_result, reflection)
            self.state.reflection_log.append(reflection.get("summary", ""))

        # 5. Aşağı etimadda avtomatik rethink
        confidence = float(reasoning_result.get("confidence", 0.0))
        used_modes = [selected_mode]

        if allow_rethink and confidence < self.LOW_CONFIDENCE_THRESHOLD:
            alt_mode = self._pick_alternative_mode(selected_mode)
            logger.info(
                f"[Brain Cycle {self.state.cycle_count}] Low confidence ({confidence:.2f}). "
                f"Rethinking with '{alt_mode}'..."
            )
            alt_reasoner = self.reasoning.get(alt_mode, self.reasoning["tot"])
            alt_result = alt_reasoner.reason(
                query=thought.content,
                context=relevant,
                goal=self.state.current_goal,
                max_steps=max_steps,
            )
            # İki nəticədən daha yüksək etimadlı olanı seç
            if float(alt_result.get("confidence", 0)) > confidence:
                reasoning_result = alt_result
                selected_mode = alt_mode
                confidence = float(alt_result.get("confidence", 0))
                self.state.last_reasoning_trace = alt_result.get("trace", [])
            used_modes.append(alt_mode)

        self.state.uncertainty = 1.0 - confidence

        # 6. Yaddaşa yaz
        self.memory["short_term"].add(thought)
        self.memory["episodic"].store_episode(
            event=thought.content,
            reasoning_trace=self.state.last_reasoning_trace,
            outcome=reasoning_result.get("conclusion"),
            metadata={
                "confidence": confidence,
                "mode": selected_mode,
                "importance": thought.importance,
            },
        )

        # 7. Qərar
        decision = self.action.decide(
            reasoning_result=reasoning_result,
            goal=self.state.current_goal,
            working_memory=self.state.working_memory,
            uncertainty=self.state.uncertainty,
        )
        self.state.last_decision = decision

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
            "meta_reflection": self.state.reflection_log[-1] if self.state.reflection_log else None,
        }

        logger.info(
            f"[Brain Cycle {self.state.cycle_count}] END | mode={selected_mode} | "
            f"conf={confidence:.3f} | unc={self.state.uncertainty:.3f} | "
            f"action={decision.get('action')}"
        )
        return result

    # ------------------------------------------------------------------
    # Attention & Memory
    # ------------------------------------------------------------------
    def _add_to_working_memory(self, thought: Thought) -> None:
        self.state.working_memory.append(thought)
        if len(self.state.working_memory) > self.MAX_WORKING_MEMORY:
            # Ən az vacib olanı sil (importance + recency)
            scored = [
                (i, t.importance * 0.6 + (i / len(self.state.working_memory)) * 0.4)
                for i, t in enumerate(self.state.working_memory)
            ]
            scored.sort(key=lambda x: x[1])
            drop_idx = scored[0][0]
            self.state.working_memory.pop(drop_idx)

    def _retrieve_with_attention(self, thought: Thought, top_k: int = 6) -> List[str]:
        short = self.memory["short_term"].retrieve(top_k=top_k)
        long_ = self.memory["long_term"].retrieve(query=thought.content, top_k=top_k)
        episodic = self.memory["episodic"].retrieve(query=thought.content, top_k=3)

        # Sadə attention: təkrarlanan və qısa olanları bir az aşağı sal
        combined = short + long_ + episodic
        seen = set()
        filtered = []
        for m in combined:
            key = str(m)[:80]
            if key not in seen:
                seen.add(key)
                filtered.append(m)
        return filtered[:top_k]

    def _estimate_importance(self, perceived: Dict[str, Any]) -> float:
        """Sadə əhəmiyyət skoru."""
        conf = float(perceived.get("confidence", 0.5))
        modality = perceived.get("modality", "text")
        boost = 0.1 if modality == "multimodal" else 0.0
        length = len(str(perceived.get("summary", "")))
        length_factor = min(0.2, length / 500)
        return round(min(1.0, conf * 0.7 + boost + length_factor), 3)

    # ------------------------------------------------------------------
    # Mode selection & Meta-cognition
    # ------------------------------------------------------------------
    def _select_mode(self, mode: str, thought: Thought, goal: Optional[str]) -> str:
        mode = (mode or "auto").lower().strip()
        if mode in ("cot", "tot", "sot"):
            return mode

        text = thought.content.lower()
        word_count = len(text.split())

        # Plan / struktur / memarlıq
        if word_count > 35 or any(
            k in text
            for k in (
                "plan",
                "addım",
                "struktur",
                "mərhələ",
                "necə qur",
                "architect",
                "roadmap",
                "layihə",
            )
        ):
            return "sot"

        # Müqayisə / seçim / alternativ
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
                "fərq",
                "üstünlük",
            )
        ):
            return "tot"

        return "cot"

    def _pick_alternative_mode(self, current: str) -> str:
        alts = {"cot": "tot", "tot": "sot", "sot": "cot"}
        return alts.get(current, "tot")

    def _meta_reflect(
        self,
        reasoning_result: Dict[str, Any],
        thought: Thought,
        context: List[str],
    ) -> Dict[str, Any]:
        """Öz düşüncə prosesinə tənqidi baxış."""
        conf = float(reasoning_result.get("confidence", 0.5))
        method = reasoning_result.get("method", "unknown")
        trace_len = len(reasoning_result.get("trace", []))

        issues = []
        if conf < self.LOW_CONFIDENCE_THRESHOLD:
            issues.append("aşağı etimad")
        if trace_len < 3:
            issues.append("qısa düşüncə izi")
        if not context:
            issues.append("kontekst zəifdir")

        if not issues:
            summary = f"Reflection: {method} stabil görünür (conf={conf:.2f})."
            quality = "good"
        else:
            summary = f"Reflection: Diqqət – {', '.join(issues)}. Method={method}."
            quality = "needs_attention"

        return {
            "summary": summary,
            "quality": quality,
            "issues": issues,
            "confidence_observed": conf,
        }

    def _apply_reflection(
        self, reasoning_result: Dict[str, Any], reflection: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Reflection nəticəsinə görə confidence-i bir az tənzimlə."""
        conf = float(reasoning_result.get("confidence", 0.5))
        if reflection.get("quality") == "needs_attention":
            # Etimadı bir qədər aşağı sal
            conf = max(0.3, conf - 0.06)
        else:
            conf = min(0.95, conf + 0.02)

        reasoning_result = dict(reasoning_result)
        reasoning_result["confidence"] = round(conf, 3)
        reasoning_result["reflection"] = reflection.get("summary")
        return reasoning_result

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------
    def set_goal(self, goal: str) -> List[str]:
        self.state.current_goal = goal
        plan = self.reasoning["planner"].create_plan(goal)
        self.state.active_plan = plan
        logger.info(f"New goal set: {goal}")
        return plan

    def remember(self, key: str, value: Any, metadata: Optional[Dict] = None) -> str:
        return self.memory["long_term"].store(key, value, metadata)

    def recall(self, query: str, top_k: int = 5) -> List[str]:
        return self.memory["long_term"].retrieve(query, top_k=top_k)

    def get_state(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "cycle_count": self.state.cycle_count,
            "current_goal": self.state.current_goal,
            "working_memory_size": len(self.state.working_memory),
            "active_plan": self.state.active_plan,
            "last_trace": self.state.last_reasoning_trace[-6:]
            if self.state.last_reasoning_trace
            else [],
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
        logger.info("ThinkingBrain fully reset.")

    def __repr__(self) -> str:
        return (
            f"ThinkingBrain(name={self.name!r}, cycles={self.state.cycle_count}, "
            f"goal={self.state.current_goal!r}, unc={self.state.uncertainty:.2f})"
        )
