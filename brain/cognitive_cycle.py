"""
Leon Cognitive Cycle — AGI-oriented control loop (not AGI itself).

PODALR:
  Perceive → Orient → Decide → Act → Learn → Reflect

Unifies ReasoningEngine, memory, agents, reflection, optional multimodal.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.persistence import write_json
from core.logger import logger


def _cycle_dir() -> Path:
    try:
        from core.config import config

        d = Path(config.path.leon_dir) / "cycles"
    except Exception:
        d = Path("data/leon/cycles")
    d.mkdir(parents=True, exist_ok=True)
    return d


class CognitiveCycle:
    """One general-purpose think-act-learn loop."""

    def __init__(self, name: str = "Leon"):
        self.name = name

    def run(
        self,
        query: str,
        *,
        goal: Optional[str] = None,
        image_path: Optional[str] = None,
        agent_type: Optional[str] = None,
        allow_experimental_agent: bool = False,
        learn: bool = True,
        reflect: bool = True,
        max_reflect_retries: int = 1,
    ) -> Dict[str, Any]:
        cycle_id = datetime.now().strftime("%Y%m%d%H%M%S")
        trace: List[Dict[str, Any]] = []

        # ----- Perceive -----
        perception = self._perceive(query, image_path=image_path)
        trace.append({"phase": "perceive", "ok": perception.get("ok", True)})

        # ----- Orient -----
        orientation = self._orient(query, perception, goal=goal)
        trace.append(
            {
                "phase": "orient",
                "task_type": orientation.get("task_type"),
                "hits": len(orientation.get("retrieval") or []),
            }
        )

        # ----- Decide (reason + optional re-reason after reflect) -----
        decision = None
        reflection = None
        attempts = 0
        mode = orientation.get("reasoning_mode") or "auto"
        while attempts <= max_reflect_retries:
            attempts += 1
            decision = self._decide(
                query,
                goal=goal or orientation.get("inferred_goal"),
                reasoning_mode=mode,
                perception=perception,
                orientation=orientation,
            )
            if not reflect:
                break
            reflection = self._reflect(decision, orientation=orientation, goal=goal)
            if reflection.get("quality") in ("good", "acceptable"):
                break
            # escalate strategy once
            if mode == "auto":
                mode = "cot"
            elif mode == "cot":
                mode = "tot"
            else:
                break

        trace.append(
            {
                "phase": "decide",
                "source": (decision or {}).get("source"),
                "confidence": (decision or {}).get("confidence"),
                "attempts": attempts,
            }
        )
        if reflection:
            trace.append(
                {
                    "phase": "reflect",
                    "quality": reflection.get("quality"),
                    "issues": reflection.get("issues"),
                }
            )
            if decision is not None:
                decision = self._apply_reflection(decision, reflection)

        # ----- Act -----
        action = self._act(
            decision,
            agent_type=agent_type or orientation.get("suggested_agent"),
            allow_experimental=allow_experimental_agent,
            query=query,
        )
        if action:
            trace.append(
                {
                    "phase": "act",
                    "agent": action.get("type"),
                    "success": action.get("success"),
                }
            )

        # ----- Learn -----
        learned = None
        if learn:
            learned = self._learn(query, decision, perception=perception)
            trace.append(
                {"phase": "learn", "stored": bool(learned and learned.get("stored"))}
            )

        report = {
            "ok": True,
            "cycle_id": cycle_id,
            "identity": self.name,
            "query": query,
            "goal": goal,
            "perception": perception,
            "orientation": orientation,
            "decision": {
                "answer": (decision or {}).get("answer")
                or (decision or {}).get("conclusion"),
                "confidence": (decision or {}).get("confidence"),
                "confidence_label": (decision or {}).get("confidence_label"),
                "source": (decision or {}).get("source"),
                "trace_id": (decision or {}).get("trace_id"),
                "conflict": (decision or {}).get("conflict"),
                "evidence_count": len((decision or {}).get("evidence") or []),
            },
            "action": action,
            "reflection": reflection,
            "learned": learned,
            "phases": trace,
            "agi_claim": False,
            "note": "Cognitive cycle prototype — not AGI",
            "at": datetime.now().isoformat(),
        }

        # convenience aliases for CLI parity with reason/think
        report["answer"] = report["decision"].get("answer")
        report["conclusion"] = report["answer"]
        report["confidence"] = report["decision"].get("confidence")
        report["source"] = report["decision"].get("source")
        report["trace_id"] = report["decision"].get("trace_id")

        write_json(_cycle_dir() / f"cycle_{cycle_id}.json", report)
        write_json(_cycle_dir() / "last_cycle.json", report)
        logger.info(
            f"CognitiveCycle {cycle_id} src={report.get('source')} conf={report.get('confidence')}"
        )
        return report

    # ------------------------------------------------------------------ phases
    def _perceive(
        self, query: str, *, image_path: Optional[str]
    ) -> Dict[str, Any]:
        out: Dict[str, Any] = {
            "ok": True,
            "text": query,
            "image": None,
            "modalities": ["text"],
        }
        if image_path:
            try:
                from multimodal.understand import understand_image

                img = understand_image(image_path, use_vlm=True, inject_facts=False)
                out["image"] = {
                    "path": image_path,
                    "summary": img.get("summary"),
                    "ok": img.get("ok"),
                    "palette": (img.get("local") or {}).get("palette_names"),
                    "vlm_ok": bool((img.get("vlm") or {}).get("ok")),
                }
                out["modalities"].append("image")
                if img.get("summary"):
                    out["enriched_query"] = f"{query}\n[image] {img['summary'][:400]}"
            except Exception as e:
                out["image"] = {"ok": False, "error": str(e), "path": image_path}
        return out

    def _orient(
        self,
        query: str,
        perception: Dict[str, Any],
        *,
        goal: Optional[str],
    ) -> Dict[str, Any]:
        q = (perception.get("enriched_query") or query).lower()
        task_type = "qa"
        suggested_agent = None
        reasoning_mode = "auto"

        if any(k in q for k in ("plan", "planlaş", "addım", "schedule")):
            task_type = "planning"
            reasoning_mode = "cot"
        elif any(k in q for k in ("kod", "code", "function", "python")):
            task_type = "coding"
            suggested_agent = "coding"
        elif any(k in q for k in ("axtar", "research", "web")):
            task_type = "research"
            suggested_agent = "research"
        elif any(k in q for k in ("səbəb", "cause", "niyə", "why")):
            task_type = "causal"
            reasoning_mode = "cot"
        elif any(k in q for k in ("əgər", "if ", "→", "nəticə")):
            task_type = "inference"
            reasoning_mode = "cot"

        retrieval = []
        try:
            from memory.retrieve import retrieve

            r = retrieve(query, top_k=6)
            retrieval = r.get("candidates") or []
        except Exception:
            pass

        return {
            "task_type": task_type,
            "reasoning_mode": reasoning_mode,
            "suggested_agent": suggested_agent,
            "inferred_goal": goal or (task_type if task_type != "qa" else None),
            "retrieval": [
                {"source": c.get("source"), "score": c.get("score"), "content": str(c.get("content") or "")[:160]}
                for c in retrieval[:6]
            ],
            "modalities": perception.get("modalities") or ["text"],
        }

    def _decide(
        self,
        query: str,
        *,
        goal: Optional[str],
        reasoning_mode: str,
        perception: Dict[str, Any],
        orientation: Dict[str, Any],
    ) -> Dict[str, Any]:
        from brain.orchestrator import BrainOrchestrator

        q = perception.get("enriched_query") or query
        orch = BrainOrchestrator(brain_name=self.name)
        return orch.run(
            q,
            goal=goal,
            reasoning_mode=reasoning_mode or "auto",
            use_session=True,
            archive_result=False,
        )

    def _reflect(
        self,
        decision: Dict[str, Any],
        *,
        orientation: Dict[str, Any],
        goal: Optional[str],
    ) -> Dict[str, Any]:
        from brain.reflection import ReflectionEngine

        eng = ReflectionEngine()
        ctx = len(orientation.get("retrieval") or [])
        report = eng.reflect(
            {
                "confidence": decision.get("confidence", 0.5),
                "method": decision.get("source"),
                "trace": decision.get("trace") or decision.get("evidence") or [],
                "llm_used": decision.get("llm_used", False),
            },
            context_size=ctx,
            goal=goal,
        )
        return {
            "quality": report.quality,
            "issues": report.issues,
            "strengths": report.strengths,
            "suggestions": report.suggestions,
            "confidence_adjustment": report.confidence_adjustment,
        }

    def _apply_reflection(
        self, decision: Dict[str, Any], reflection: Dict[str, Any]
    ) -> Dict[str, Any]:
        from brain.reflection import ReflectionEngine, ReflectionReport

        eng = ReflectionEngine()
        rr = ReflectionReport(
            cycle=0,
            quality=reflection.get("quality") or "acceptable",
            issues=list(reflection.get("issues") or []),
            strengths=list(reflection.get("strengths") or []),
            suggestions=list(reflection.get("suggestions") or []),
            confidence_adjustment=float(reflection.get("confidence_adjustment") or 0),
        )
        return eng.apply(decision, rr)

    def _act(
        self,
        decision: Optional[Dict[str, Any]],
        *,
        agent_type: Optional[str],
        allow_experimental: bool,
        query: str,
    ) -> Optional[Dict[str, Any]]:
        if not agent_type:
            return None
        try:
            from agents.manager import agent_manager

            agent = agent_manager.create(
                agent_type, allow_experimental=allow_experimental or agent_type in ("react", "coding")
            )
            task = (decision or {}).get("conclusion") or (decision or {}).get("answer") or query
            res = agent_manager.run(agent.id, str(task))
            return {
                "type": agent_type,
                "success": res.success,
                "output": res.output,
                "error": res.error,
            }
        except Exception as e:
            return {"type": agent_type, "success": False, "error": str(e)}

    def _learn(
        self,
        query: str,
        decision: Optional[Dict[str, Any]],
        *,
        perception: Dict[str, Any],
    ) -> Dict[str, Any]:
        answer = (decision or {}).get("answer") or (decision or {}).get("conclusion")
        conf = float((decision or {}).get("confidence") or 0)
        source = (decision or {}).get("source") or ""
        if not answer or answer == "UNKNOWN" or conf < 0.55:
            return {"stored": False, "reason": "low confidence or UNKNOWN"}
        if source in ("llm", "fallback") and conf < 0.75:
            return {"stored": False, "reason": "unverified llm/fallback"}

        stored = []
        try:
            from knowledge.registry import get_fact_store

            fs = get_fact_store()
            stmt = f"{query.strip()[:120]} → {str(answer)[:200]}"
            fs.add(stmt, source=f"cycle:{source}", confidence=min(0.9, conf))
            stored.append("fact")
        except Exception:
            pass
        try:
            from memory import MemoryManager

            MemoryManager().remember(str(answer)[:400], kind="vector")
            stored.append("vector")
        except Exception:
            pass
        return {"stored": bool(stored), "targets": stored}


cognitive_cycle = CognitiveCycle()


def cycle(query: str, **kw) -> Dict[str, Any]:
    return CognitiveCycle().run(query, **kw)
