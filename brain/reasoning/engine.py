"""
Reasoning Engine (spec 020).

Parse → Retrieve → Rank → Infer → Validate → Confidence → Trace
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid

from core.logger import logger
from core.event_bus import event_bus


@dataclass
class ReasoningTrace:
    trace_id: str
    query: str
    retrieved_nodes: List[str] = field(default_factory=list)
    rules_applied: List[str] = field(default_factory=list)
    candidate_conclusions: List[str] = field(default_factory=list)
    selected_conclusion: Optional[str] = None
    confidence: float = 0.0
    validation: str = "ok"
    strategy: str = "deduction"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "query": self.query,
            "retrieved_nodes": self.retrieved_nodes,
            "rules_applied": self.rules_applied,
            "candidate_conclusions": self.candidate_conclusions,
            "selected_conclusion": self.selected_conclusion,
            "confidence": self.confidence,
            "validation": self.validation,
            "strategy": self.strategy,
            "timestamp": self.timestamp,
        }


class ReasoningEngine:
    """Spec 020 — justified conclusions with traces."""

    def __init__(self):
        self._traces: Dict[str, ReasoningTrace] = {}
        self._brain = None

    def reason(
        self,
        request: str,
        strategy: str = "auto",
        goal: Optional[str] = None,
        use_brain: bool = True,
    ) -> Dict[str, Any]:
        trace_id = "TR-" + str(uuid.uuid4())[:8]
        retrieved = self._retrieve(request)
        strategy = self._pick_strategy(request, strategy)

        candidates: List[str] = []
        confidence = 0.5
        llm_used = False
        method = strategy

        # Curriculum / train short-circuit
        from_curriculum = self._try_curriculum(request)
        if from_curriculum:
            candidates.append(from_curriculum)
            confidence = 0.92
            method = "deduction"

        if use_brain:
            try:
                if self._brain is None:
                    from brain.core_brain import ThinkingBrain
                    self._brain = ThinkingBrain(name="Leon")
                mode = {"deduction": "cot", "induction": "tot", "abduction": "tot", "analogy": "sot"}.get(
                    strategy, "auto"
                )
                result = self._brain.think(request, goal=goal, reasoning_mode=mode)
                conclusion = str(result.get("conclusion") or "")
                if conclusion:
                    candidates.append(conclusion)
                confidence = max(confidence, float(result.get("confidence") or 0.5))
                llm_used = bool(result.get("llm_used"))
                method = result.get("reasoning_mode") or method
            except Exception as e:
                logger.warning(f"ReasoningEngine brain fallback: {e}")

        if not candidates:
            candidates.append("UNKNOWN")
            confidence = 0.0

        selected = candidates[0]
        validation = "ok" if selected != "UNKNOWN" else "unresolved_conflict"

        # Confidence model (spec 007)
        conf = self._score_confidence(
            evidence_quality=0.8 if retrieved else 0.4,
            source_reliability=0.9 if from_curriculum else 0.6,
            consistency=0.85 if validation == "ok" else 0.3,
            base=confidence,
        )

        trace = ReasoningTrace(
            trace_id=trace_id,
            query=request,
            retrieved_nodes=retrieved[:10],
            rules_applied=[strategy],
            candidate_conclusions=candidates[:5],
            selected_conclusion=selected,
            confidence=conf,
            validation=validation,
            strategy=strategy,
        )
        self._traces[trace_id] = trace

        event_bus.publish(
            "ReasoningCompleted",
            {"trace_id": trace_id, "confidence": conf},
            source="reasoning_engine",
        )

        return {
            "answer": selected,
            "confidence": conf,
            "trace_id": trace_id,
            "trace": trace.to_dict(),
            "strategy": strategy,
            "llm_used": llm_used,
            "memory_actions": [],
        }

    def _retrieve(self, query: str) -> List[str]:
        hits: List[str] = []
        try:
            from knowledge import KnowledgeRetrieval
            kr = KnowledgeRetrieval()
            r = kr.retrieve(query, top_k=5)
            for f in r.get("facts", [])[:5]:
                hits.append(f["statement"] if isinstance(f, dict) else str(f))
            for n in r.get("nodes", [])[:3]:
                hits.append(n.get("label", str(n)))
        except Exception:
            pass
        try:
            from memory import MemoryManager
            mem = MemoryManager()
            recalled = mem.recall(query, top_k=3)
            for text, _ in recalled.get("vector", [])[:3]:
                hits.append(text)
        except Exception:
            pass
        return hits

    def _try_curriculum(self, request: str) -> Optional[str]:
        try:
            from curriculum import CurriculumEngine
            ans = CurriculumEngine().ask(request)
            if ans.get("matched") and ans.get("answer"):
                return str(ans["answer"])
        except Exception:
            pass
        return None

    def _pick_strategy(self, request: str, strategy: str) -> str:
        s = (strategy or "auto").lower()
        if s in ("deduction", "induction", "abduction", "analogy"):
            return s
        low = request.lower()
        if any(k in low for k in ("niyə", "why", "izah", "səbəb")):
            return "abduction"
        if any(k in low for k in ("ümumi", "pattern", "oxşar", "like")):
            return "induction"
        if any(k in low for k in ("müqayisə", "analog")):
            return "analogy"
        return "deduction"

    def _score_confidence(
        self,
        evidence_quality: float,
        source_reliability: float,
        consistency: float,
        base: float,
    ) -> float:
        # spec 020: evidence × source × consistency, blended with base
        product = evidence_quality * source_reliability * consistency
        conf = 0.5 * product + 0.5 * base
        return round(max(0.0, min(1.0, conf)), 3)

    def get_trace(self, trace_id: str) -> Optional[Dict[str, Any]]:
        t = self._traces.get(trace_id)
        return t.to_dict() if t else None


reasoning_engine = ReasoningEngine()
