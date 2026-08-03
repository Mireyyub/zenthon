"""
Reasoning Engine (spec 020) — LEON vahid düşüncə yolu.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import uuid

from core.logger import logger
from core.event_bus import event_bus
from core.persistence import write_json, read_json
from brain.confidence import composite_confidence, action_from_confidence, label_confidence


@dataclass
class EvidenceItem:
    kind: str
    content: str
    weight: float = 0.5
    ref: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "kind": self.kind,
            "content": self.content[:400],
            "weight": self.weight,
            "ref": self.ref,
        }


@dataclass
class ReasoningTrace:
    trace_id: str
    query: str
    retrieved_nodes: List[str] = field(default_factory=list)
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    rules_applied: List[str] = field(default_factory=list)
    candidate_conclusions: List[str] = field(default_factory=list)
    selected_conclusion: Optional[str] = None
    confidence: float = 0.0
    confidence_label: str = "Unknown"
    validation: str = "ok"
    strategy: str = "deduction"
    source: str = "unknown"
    llm_used: bool = False
    conflict: Optional[str] = None
    decision: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "query": self.query,
            "retrieved_nodes": self.retrieved_nodes,
            "evidence": self.evidence,
            "rules_applied": self.rules_applied,
            "candidate_conclusions": self.candidate_conclusions,
            "selected_conclusion": self.selected_conclusion,
            "confidence": self.confidence,
            "confidence_label": self.confidence_label,
            "validation": self.validation,
            "strategy": self.strategy,
            "source": self.source,
            "llm_used": self.llm_used,
            "conflict": self.conflict,
            "decision": self.decision,
            "timestamp": self.timestamp,
        }


def _traces_dir() -> Path:
    try:
        from core.config import config

        return Path(config.path.traces_dir)
    except Exception:
        return Path("data/leon/traces")


class ReasoningEngine:
    def __init__(self, persist_traces: bool = True):
        self._traces: Dict[str, ReasoningTrace] = {}
        self._brain = None
        self.persist_traces = persist_traces

    def reason(
        self,
        request: str,
        strategy: str = "auto",
        goal: Optional[str] = None,
        use_brain: bool = True,
        reasoning_mode: Optional[str] = None,
    ) -> Dict[str, Any]:
        trace_id = "TR-" + str(uuid.uuid4())[:8]
        evidence: List[EvidenceItem] = []
        candidates: List[Tuple[str, str, float]] = []

        strategy = self._pick_strategy(request, strategy)
        retrieved = self._retrieve(request, evidence)

        curr = self._try_curriculum(request)
        if curr:
            ans, src = curr
            candidates.append((ans, src, 0.92))
            evidence.append(
                EvidenceItem(kind="curriculum", content=f"{src}: {ans}", weight=0.95, ref=src)
            )

        llm_used = False
        brain_method = strategy
        if use_brain and (not candidates or reasoning_mode):
            try:
                if self._brain is None:
                    from brain.core_brain import ThinkingBrain
                    from core.config import config

                    self._brain = ThinkingBrain(name=getattr(config, "ai_name", "Leon") or "Leon")
                mode = reasoning_mode or {
                    "deduction": "cot",
                    "induction": "tot",
                    "abduction": "tot",
                    "analogy": "sot",
                }.get(strategy, "auto")
                result = self._brain.think(request, goal=goal, reasoning_mode=mode)
                conclusion = str(result.get("conclusion") or "").strip()
                if conclusion:
                    candidates.append((conclusion, "llm", float(result.get("confidence") or 0.55)))
                    evidence.append(
                        EvidenceItem(
                            kind="llm",
                            content=conclusion[:300],
                            weight=0.55,
                            ref=result.get("reasoning_mode") or "llm",
                        )
                    )
                llm_used = bool(result.get("llm_used"))
                brain_method = result.get("reasoning_mode") or brain_method
            except Exception as e:
                logger.warning(f"ReasoningEngine brain: {e}")

        selected, source, validation, conflict = self._resolve_conflict(candidates)

        eq = min(1.0, 0.35 + 0.12 * len(evidence) + (0.25 if retrieved else 0))
        src_rel = {
            "curriculum": 0.95,
            "train": 0.9,
            "eval": 0.9,
            "facts": 0.85,
            "graph": 0.82,
            "llm": 0.6,
            "unknown": 0.4,
        }.get(source.split(":")[0] if source else "unknown", 0.5)
        consistency = 0.9 if validation == "ok" else (0.45 if validation == "conflict" else 0.2)
        base = candidates[0][2] if candidates else 0.0

        conf_pack = composite_confidence(
            base=base,
            evidence_quality=eq,
            source_reliability=src_rel,
            consistency=consistency,
            method=source.split(":")[0] if source and source != "llm" else (brain_method or "unknown"),
            has_goal=goal is not None,
            memory_hits=len(retrieved),
            uncertainty=0.0 if validation == "ok" else 0.4,
        )
        conf = conf_pack["score"]
        decision = action_from_confidence(conf)
        decision["confidence"] = conf
        decision["confidence_label"] = conf_pack["label"]
        decision["composite"] = conf_pack

        if selected == "UNKNOWN":
            decision["action"] = "rethink"
            decision["message"] = conflict or "Kifayət qədər evidence yoxdur."

        method_for_trace = brain_method if llm_used else strategy
        trace = ReasoningTrace(
            trace_id=trace_id,
            query=request,
            retrieved_nodes=retrieved[:12],
            evidence=[e.to_dict() for e in evidence],
            rules_applied=[strategy, f"source={source}"],
            candidate_conclusions=[c[0][:200] for c in candidates[:5]],
            selected_conclusion=selected,
            confidence=conf,
            confidence_label=conf_pack["label"],
            validation=validation,
            strategy=method_for_trace,
            source=source,
            llm_used=llm_used,
            conflict=conflict,
            decision=decision,
        )
        self._traces[trace_id] = trace
        if self.persist_traces:
            self._save_trace(trace)

        event_bus.publish(
            "ReasoningCompleted",
            {"trace_id": trace_id, "confidence": conf, "source": source},
            source="reasoning_engine",
        )

        return {
            "answer": selected,
            "conclusion": selected,
            "confidence": conf,
            "confidence_label": conf_pack["label"],
            "trace_id": trace_id,
            "trace": trace.to_dict(),
            "evidence": [e.to_dict() for e in evidence],
            "strategy": strategy,
            "reasoning_mode": method_for_trace,
            "source": source,
            "llm_used": llm_used,
            "validation": validation,
            "conflict": conflict,
            "decision": decision,
            "memory_actions": [],
        }

    def _resolve_conflict(
        self, candidates: List[Tuple[str, str, float]]
    ) -> Tuple[str, str, str, Optional[str]]:
        if not candidates:
            return "UNKNOWN", "unknown", "unresolved", "Heç bir namizəd yoxdur"

        priority = {
            "curriculum": 100,
            "train": 90,
            "eval": 90,
            "facts": 80,
            "graph": 70,
            "llm": 40,
            "unknown": 10,
        }

        def prio(src: str) -> int:
            return priority.get(src.split(":")[0], 10)

        candidates_sorted = sorted(candidates, key=lambda c: (prio(c[1]), c[2]), reverse=True)
        best_text, best_src, _ = candidates_sorted[0]

        def polarity(t: str) -> Optional[str]:
            tl = t.lower().strip()
            if tl.startswith("bəli") or tl.startswith("yes"):
                return "yes"
            if tl.startswith("xeyr") or tl.startswith("no"):
                return "no"
            return None

        best_pol = polarity(best_text)
        for text, src, _ in candidates_sorted[1:]:
            if prio(src) >= 80 and prio(best_src) >= 80:
                pol = polarity(text)
                if best_pol and pol and best_pol != pol:
                    msg = f"Konflikt: '{best_text[:80]}' ({best_src}) vs '{text[:80]}' ({src})"
                    return "UNKNOWN", "conflict", "conflict", msg

        return best_text, best_src, "ok", None

    def _retrieve(self, query: str, evidence: List[EvidenceItem]) -> List[str]:
        hits: List[str] = []
        try:
            from knowledge.registry import get_fact_store

            for f in get_fact_store().search(query, top_k=5):
                stmt = f.get("statement", "")
                hits.append(stmt)
                evidence.append(
                    EvidenceItem(kind="fact", content=stmt, weight=0.75, ref=f.get("id", ""))
                )
        except Exception:
            pass
        try:
            from knowledge.registry import get_graph

            kg = get_graph()
            for n in kg.query(query, top_k=5):
                label = n.get("label", "")
                hits.append(label)
                evidence.append(
                    EvidenceItem(kind="graph", content=label, weight=0.7, ref=n.get("id", ""))
                )
        except Exception:
            pass
        try:
            from memory import MemoryManager

            recalled = MemoryManager().recall(query, top_k=3)
            for text, score in recalled.get("vector", [])[:3]:
                hits.append(text)
                evidence.append(
                    EvidenceItem(
                        kind="memory", content=text, weight=float(score) if score else 0.5, ref="vector"
                    )
                )
        except Exception:
            pass
        return hits

    def _try_curriculum(self, request: str) -> Optional[Tuple[str, str]]:
        try:
            from curriculum import CurriculumEngine

            ans = CurriculumEngine().ask(request)
            if ans.get("matched") and ans.get("answer") is not None:
                return str(ans["answer"]), str(ans.get("source") or "curriculum")
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

    def _save_trace(self, trace: ReasoningTrace) -> None:
        try:
            path = _traces_dir() / f"{trace.trace_id}.json"
            write_json(path, trace.to_dict())
        except Exception as e:
            logger.debug(f"trace persist: {e}")

    def get_trace(self, trace_id: str) -> Optional[Dict[str, Any]]:
        if trace_id in self._traces:
            return self._traces[trace_id].to_dict()
        path = _traces_dir() / f"{trace_id}.json"
        data = read_json(path, default=None)
        return data if isinstance(data, dict) else None


reasoning_engine = ReasoningEngine()
