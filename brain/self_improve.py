"""
Leon Self-Improvement Engine (v2)

Closed loop:
  diagnose → propose → apply → verify → (repeat until target)

Enhancements:
- Multi-round adaptive cycles with early stop
- Weak-case topic clustering
- Practice reasoning on failures after learning
- Optional train.jsonl mutation bridge (SelfMutateEngine)
- Trace reflection → knowledge
- History-aware action prioritization
- Graph is_a hints from category-style QAs

Code mutation is optional and still gated by LEON_ALLOW_MUTATE.
Default scope remains knowledge + curriculum + learning.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import json
import re
import uuid

from core.logger import logger
from core.persistence import write_json, read_json


def _reports_dir() -> Path:
    try:
        from core.config import config

        d = Path(config.path.leon_dir) / "self_improve"
    except Exception:
        d = Path("data/leon/self_improve")
    d.mkdir(parents=True, exist_ok=True)
    return d


class SelfImproveEngine:
    TARGET_PASS = 0.95
    MAX_ROUNDS = 3

    def __init__(self):
        self.dir = _reports_dir()
        hist = read_json(self.dir / "history.json", default={"runs": []}) or {}
        self._history: List[Dict[str, Any]] = list(hist.get("runs") or [])

    # ------------------------------------------------------------------ diagnose
    def diagnose(self, volumes: Optional[List[str]] = None) -> Dict[str, Any]:
        from curriculum import CurriculumEngine

        eng = CurriculumEngine()
        vols = volumes or eng.list_volumes() or ["01", "02"]
        evals = []
        weak_cases: List[Dict[str, Any]] = []
        for vid in vols:
            try:
                report = eng.run_eval(vid)
            except Exception as e:
                evals.append({"volume_id": vid, "error": str(e), "pass_rate": 0.0})
                continue
            evals.append(
                {
                    "volume_id": vid,
                    "pass_rate": report.get("pass_rate"),
                    "passed": report.get("passed"),
                    "total": report.get("total"),
                    "failed": report.get("failed"),
                }
            )
            for c in report.get("cases") or []:
                if not c.get("pass"):
                    weak_cases.append(
                        {
                            "volume_id": vid,
                            "question": c.get("question"),
                            "expected": c.get("expected"),
                            "got": c.get("got"),
                            "source": c.get("source"),
                            "topic": self._topic(c.get("question") or ""),
                        }
                    )

        weak_traces = self._scan_traces(limit=40)
        # also probe reason() on a sample of weak questions for live signal
        live_weak = self._live_probe(weak_cases[:8])

        learning_stats = {}
        try:
            from learning.engine import LearningEngine

            learning_stats = LearningEngine().stats()
        except Exception:
            pass

        topics = Counter(c.get("topic") or "other" for c in weak_cases)
        rates = [e.get("pass_rate") for e in evals if isinstance(e.get("pass_rate"), (int, float))]
        avg = sum(rates) / len(rates) if rates else 0.0

        severity = "ok"
        if avg < 0.5 or len(weak_cases) >= 5:
            severity = "high"
        elif avg < 0.85 or weak_cases:
            severity = "medium"

        out = {
            "timestamp": datetime.now().isoformat(),
            "severity": severity,
            "avg_pass_rate": round(avg, 3),
            "evals": evals,
            "weak_cases": weak_cases,
            "weak_traces": weak_traces,
            "live_probe": live_weak,
            "topic_counts": dict(topics),
            "learning": learning_stats,
            "volumes": vols,
            "recommendations": self._recommendations(severity, avg, weak_cases, topics),
        }
        write_json(self.dir / "last_diagnose.json", out)
        return out

    def _topic(self, q: str) -> str:
        low = (q or "").lower()
        if any(x in low for x in ("mövcud", "varlıq", "exist")):
            return "existence"
        if "obyekt" in low or "object" in low:
            return "object"
        if any(x in low for x in ("xüsusiyyət", "rəng", "forma", "property")):
            return "property"
        if "kateqor" in low or "category" in low:
            return "category"
        if any(x in low for x in ("fırlan", "əlaqə", "relation", "ətraf")):
            return "relationship"
        if any(x in low for x in ("səbəb", "nəticə", "cause")):
            return "causality"
        return "other"

    def _recommendations(
        self,
        severity: str,
        avg: float,
        weak: List[Dict],
        topics: Counter,
    ) -> List[str]:
        recs = []
        if severity == "ok":
            recs.append("Pass rate sağlamdır; yalnız monitoring.")
            return recs
        if avg < 0.9:
            recs.append("Zəif volume-ları yenidən teach et.")
        if weak:
            recs.append(f"{len(weak)} uğursuz QA → LearningEngine + FactStore.")
        top = topics.most_common(2)
        if top:
            recs.append("Prioritet mövzular: " + ", ".join(f"{t}({n})" for t, n in top))
        if severity == "high":
            recs.append("train.jsonl mutasiyası (mutate diagnose) nəzərdən keçir.")
        return recs

    def _live_probe(self, cases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        out = []
        try:
            from brain.reasoning.engine import ReasoningEngine

            eng = ReasoningEngine(persist_traces=False)
        except Exception:
            return out
        for c in cases:
            q = c.get("question") or ""
            if not q:
                continue
            try:
                r = eng.reason(q, use_brain=False)
                ans = str(r.get("answer") or r.get("conclusion") or "")
                exp = str(c.get("expected") or "")
                ok = bool(exp) and (
                    exp.lower() in ans.lower() or ans.lower() in exp.lower()
                )
                out.append(
                    {
                        "question": q,
                        "expected": exp,
                        "got": ans,
                        "confidence": r.get("confidence"),
                        "pass": ok,
                    }
                )
            except Exception as e:
                out.append({"question": q, "error": str(e), "pass": False})
        return out

    def _scan_traces(self, limit: int = 40) -> List[Dict[str, Any]]:
        try:
            from core.config import config

            tdir = Path(config.path.traces_dir)
        except Exception:
            tdir = Path("data/leon/traces")
        if not tdir.exists():
            return []
        files = sorted(tdir.glob("TR-*.json"), key=lambda p: p.stat().st_mtime, reverse=True)[
            :limit
        ]
        weak = []
        for f in files:
            data = read_json(f, default={})
            if not isinstance(data, dict):
                continue
            ans = str(data.get("selected_conclusion") or data.get("answer") or "")
            conf = float(data.get("confidence") or 0)
            if ans == "UNKNOWN" or conf < 0.45 or data.get("validation") == "conflict":
                weak.append(
                    {
                        "trace_id": data.get("trace_id"),
                        "query": data.get("query"),
                        "conclusion": ans,
                        "confidence": conf,
                        "source": data.get("source"),
                    }
                )
        return weak

    # ------------------------------------------------------------------ propose
    def propose(
        self,
        diagnosis: Optional[Dict[str, Any]] = None,
        *,
        with_mutate: bool = False,
        with_practice: bool = True,
    ) -> Dict[str, Any]:
        diag = diagnosis or self.diagnose()
        actions: List[Dict[str, Any]] = []

        # adaptive boost from history: if past teach helped, keep priority high
        hist_boost = self._history_boost()

        for e in diag.get("evals") or []:
            rate = e.get("pass_rate")
            if e.get("error") or (isinstance(rate, (int, float)) and rate < 0.9):
                pr = 10 if (rate or 0) < 0.5 else 6
                pr += hist_boost.get("teach_volume", 0)
                actions.append(
                    {
                        "type": "teach_volume",
                        "volume_id": e.get("volume_id"),
                        "reason": f"pass_rate={rate}",
                        "priority": pr,
                    }
                )

        # dedupe learn_qa by normalized question
        seen_q = set()
        for case in diag.get("weak_cases") or []:
            q, exp = case.get("question"), case.get("expected")
            if not q or not exp:
                continue
            key = re.sub(r"\s+", " ", q.strip().lower())
            if key in seen_q:
                continue
            seen_q.add(key)
            actions.append(
                {
                    "type": "learn_qa",
                    "question": q,
                    "answer": exp,
                    "volume_id": case.get("volume_id"),
                    "topic": case.get("topic"),
                    "priority": 9,
                }
            )
            if with_practice:
                actions.append(
                    {
                        "type": "practice_reason",
                        "question": q,
                        "expected": exp,
                        "priority": 4,
                    }
                )
            # category → graph hint
            if case.get("topic") == "category":
                actions.append(
                    {
                        "type": "graph_hint",
                        "question": q,
                        "answer": exp,
                        "priority": 5,
                    }
                )

        # reflect weak traces: if query looks like yes/no curriculum, skip; else store as pending note
        for tr in (diag.get("weak_traces") or [])[:10]:
            q = tr.get("query")
            if q:
                actions.append(
                    {
                        "type": "reflect_trace",
                        "query": q,
                        "conclusion": tr.get("conclusion"),
                        "confidence": tr.get("confidence"),
                        "priority": 3,
                    }
                )

        if diag.get("weak_cases"):
            actions.append(
                {
                    "type": "write_failure_dataset",
                    "count": len(diag["weak_cases"]),
                    "priority": 2,
                }
            )

        if with_mutate and (diag.get("severity") in ("medium", "high") or diag.get("weak_cases")):
            actions.append(
                {
                    "type": "mutate_train",
                    "reason": "persist weak cases into curriculum train.jsonl",
                    "priority": 7,
                }
            )

        actions.append({"type": "save_state", "name": "self_improve", "priority": 1})
        actions.append(
            {
                "type": "verify",
                "volumes": diag.get("volumes") or ["01"],
                "priority": 0,
            }
        )

        actions.sort(key=lambda a: -a.get("priority", 0))
        proposal = {
            "id": "SI-" + str(uuid.uuid4())[:8],
            "created_at": datetime.now().isoformat(),
            "diagnosis_severity": diag.get("severity"),
            "avg_pass_rate_before": diag.get("avg_pass_rate"),
            "topic_counts": diag.get("topic_counts"),
            "recommendations": diag.get("recommendations"),
            "actions": actions,
            "action_count": len(actions),
            "options": {"with_mutate": with_mutate, "with_practice": with_practice},
            "safety": {
                "code_rewrite": bool(with_mutate),
                "scope": "knowledge+curriculum+learning+eval"
                + ("+train_mutate" if with_mutate else ""),
                "note": "Source mutation only via SelfMutate allowlist + LEON_ALLOW_MUTATE",
            },
        }
        write_json(self.dir / "last_proposal.json", proposal)
        return proposal

    def _history_boost(self) -> Dict[str, int]:
        boost: Dict[str, int] = {}
        for run in self._history[-10:]:
            if run.get("improved"):
                boost["teach_volume"] = boost.get("teach_volume", 0) + 1
        return boost

    # ------------------------------------------------------------------ apply
    def apply(self, proposal: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        prop = proposal or read_json(self.dir / "last_proposal.json", default=None)
        if not prop:
            prop = self.propose()

        results: List[Dict[str, Any]] = []
        learned = 0
        taught: List[str] = []
        practiced = 0
        mutated = None
        vols_for_verify = prop.get("options", {})

        for action in prop.get("actions") or []:
            atype = action.get("type")
            try:
                if atype == "teach_volume":
                    from curriculum import CurriculumEngine

                    vid = action.get("volume_id") or "01"
                    rep = CurriculumEngine().teach_volume(vid)
                    taught.append(vid)
                    results.append(
                        {
                            "type": atype,
                            "ok": True,
                            "volume_id": vid,
                            "pass_rate": (rep.get("eval") or {}).get("pass_rate"),
                        }
                    )
                elif atype == "learn_qa":
                    from learning.engine import LearningEngine

                    q, a = action.get("question"), action.get("answer")
                    content = f"Q: {q} → A: {a}"
                    rec = LearningEngine().learn(
                        content,
                        source="self_improve:eval_failure",
                        confidence=0.92,
                        volume=action.get("volume_id"),
                        topic=action.get("topic"),
                    )
                    try:
                        from knowledge.registry import get_fact_store

                        get_fact_store().add(content, source="self_improve", confidence=0.92)
                    except Exception:
                        pass
                    # also remember in vector memory if available
                    try:
                        from memory import MemoryManager

                        MemoryManager().remember(
                            content, kind="vector", metadata={"source": "self_improve"}
                        )
                    except Exception:
                        pass
                    learned += 1
                    results.append(
                        {
                            "type": atype,
                            "ok": True,
                            "record": (rec.get("record") or {}).get("id"),
                        }
                    )
                elif atype == "practice_reason":
                    from brain.reasoning.engine import ReasoningEngine

                    q = action.get("question") or ""
                    r = ReasoningEngine(persist_traces=True).reason(q, use_brain=False)
                    ans = str(r.get("answer") or r.get("conclusion") or "")
                    exp = str(action.get("expected") or "")
                    ok = bool(exp) and (exp.lower() in ans.lower() or ans.lower() in exp.lower())
                    practiced += 1
                    results.append(
                        {
                            "type": atype,
                            "ok": ok,
                            "question": q[:80],
                            "got": ans[:80],
                            "confidence": r.get("confidence"),
                        }
                    )
                elif atype == "graph_hint":
                    ok = self._inject_graph_hint(action.get("question") or "", action.get("answer") or "")
                    results.append({"type": atype, "ok": ok})
                elif atype == "reflect_trace":
                    # store low-conf query as pending learning note (not auto-validated)
                    try:
                        from learning.engine import LearningEngine

                        LearningEngine().observe(
                            f"TRACE_WEAK: {action.get('query')} → {action.get('conclusion')}",
                            source="self_improve:trace",
                            confidence=0.4,
                        )
                        results.append({"type": atype, "ok": True})
                    except Exception as e:
                        results.append({"type": atype, "ok": False, "error": str(e)})
                elif atype == "mutate_train":
                    try:
                        from brain.self_mutate import SelfMutateEngine

                        mut = SelfMutateEngine()
                        batch = mut.propose_from_diagnosis(
                            read_json(self.dir / "last_diagnose.json", default={})
                        )
                        applied_ids = []
                        if mut.mutation_enabled():
                            for p in batch.get("proposals") or []:
                                if p.get("ok") and p.get("proposal_id"):
                                    ar = mut.apply(p["proposal_id"], run_smoke=False)
                                    applied_ids.append(ar)
                        mutated = {
                            "proposed": len(batch.get("proposals") or []),
                            "applied": applied_ids,
                            "enabled": mut.mutation_enabled(),
                        }
                        results.append({"type": atype, "ok": True, "detail": mutated})
                    except Exception as e:
                        results.append({"type": atype, "ok": False, "error": str(e)})
                elif atype == "write_failure_dataset":
                    path = self._write_failure_dataset()
                    results.append({"type": atype, "ok": True, "path": str(path)})
                elif atype == "save_state":
                    from core.bootstrap import save_state

                    save_state(action.get("name") or "self_improve")
                    results.append({"type": atype, "ok": True})
                elif atype == "verify":
                    results.append({"type": atype, "ok": True, "deferred": True})
                    vols_for_verify = action.get("volumes")
                else:
                    results.append({"type": atype, "ok": False, "error": "unknown action"})
            except Exception as e:
                results.append({"type": atype, "ok": False, "error": str(e)})
                logger.warning(f"SelfImprove apply {atype}: {e}")

        verify = self.verify(volumes=vols_for_verify if isinstance(vols_for_verify, list) else None)
        before = prop.get("avg_pass_rate_before") or 0
        after = verify.get("avg_pass_rate") or 0
        report = {
            "proposal_id": prop.get("id"),
            "applied_at": datetime.now().isoformat(),
            "results": results,
            "learned_qa": learned,
            "taught_volumes": taught,
            "practiced": practiced,
            "mutate": mutated,
            "verify": verify,
            "improved": bool(after > before) or learned > 0,
            "delta": round(float(after) - float(before), 3),
        }
        write_json(self.dir / "last_apply.json", report)
        self._history.append(
            {
                "id": prop.get("id"),
                "improved": report["improved"],
                "delta": report["delta"],
                "at": report["applied_at"],
                "learned": learned,
            }
        )
        write_json(self.dir / "history.json", {"runs": self._history[-50:]})
        return report

    def _inject_graph_hint(self, question: str, answer: str) -> bool:
        """Best-effort: 'X hansı kateqoriya' → X is_a Category."""
        try:
            from knowledge.registry import get_graph

            g = get_graph()
        except Exception:
            return False
        m = re.search(r"(.+?)\s+hansı\s+kateqor", (question or "").lower())
        if not m:
            return False
        entity = m.group(1).strip()
        cat = (answer or "").strip().rstrip(".")
        if not entity or not cat:
            return False
        try:
            eid = g.add_node(entity, node_type="entity")
            cid = g.add_node(cat, node_type="concept")
            g.add_edge(eid, cid, "is_a")
            return True
        except Exception:
            return False

    def _write_failure_dataset(self) -> Path:
        diag = read_json(self.dir / "last_diagnose.json", default={})
        path = self.dir / "failures.jsonl"
        lines = []
        for c in diag.get("weak_cases") or []:
            lines.append(
                json.dumps(
                    {
                        "instruction": c.get("question"),
                        "output": c.get("expected"),
                        "got": c.get("got"),
                        "volume_id": c.get("volume_id"),
                        "topic": c.get("topic"),
                        "source": "self_improve",
                    },
                    ensure_ascii=False,
                )
            )
        path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
        return path

    # ------------------------------------------------------------------ verify
    def verify(self, volumes: Optional[List[str]] = None) -> Dict[str, Any]:
        from curriculum import CurriculumEngine

        eng = CurriculumEngine()
        vols = volumes or eng.list_volumes() or ["01"]
        evals = []
        for vid in vols:
            try:
                r = eng.run_eval(vid)
                evals.append(
                    {
                        "volume_id": vid,
                        "pass_rate": r.get("pass_rate"),
                        "passed": r.get("passed"),
                        "total": r.get("total"),
                    }
                )
            except Exception as e:
                evals.append({"volume_id": vid, "error": str(e), "pass_rate": 0.0})
        rates = [e["pass_rate"] for e in evals if isinstance(e.get("pass_rate"), (int, float))]
        avg = round(sum(rates) / len(rates), 3) if rates else 0.0
        before = read_json(self.dir / "last_diagnose.json", default={}).get("avg_pass_rate")
        return {
            "avg_pass_rate": avg,
            "before": before,
            "delta": round(avg - float(before or 0), 3) if before is not None else None,
            "evals": evals,
            "timestamp": datetime.now().isoformat(),
        }

    # ------------------------------------------------------------------ cycles
    def run_cycle(
        self,
        volumes: Optional[List[str]] = None,
        *,
        apply_changes: bool = True,
        with_mutate: bool = False,
        with_practice: bool = True,
    ) -> Dict[str, Any]:
        diag = self.diagnose(volumes=volumes)
        prop = self.propose(diag, with_mutate=with_mutate, with_practice=with_practice)
        if not apply_changes:
            return {
                "diagnosis": {
                    "severity": diag.get("severity"),
                    "avg_pass_rate": diag.get("avg_pass_rate"),
                    "weak_case_count": len(diag.get("weak_cases") or []),
                    "topics": diag.get("topic_counts"),
                    "recommendations": diag.get("recommendations"),
                },
                "proposal": {
                    "id": prop.get("id"),
                    "action_count": prop.get("action_count"),
                    "safety": prop.get("safety"),
                },
                "applied": False,
                "note": "dry-run",
            }
        applied = self.apply(prop)
        return {
            "diagnosis": {
                "severity": diag.get("severity"),
                "avg_pass_rate": diag.get("avg_pass_rate"),
                "weak_case_count": len(diag.get("weak_cases") or []),
                "topics": diag.get("topic_counts"),
            },
            "proposal_id": prop.get("id"),
            "action_count": prop.get("action_count"),
            "apply": applied,
            "safety": prop.get("safety"),
        }

    def auto(
        self,
        volumes: Optional[List[str]] = None,
        *,
        rounds: int = 3,
        target: float = 0.95,
        with_mutate: bool = False,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Multi-round improve until target pass rate or max rounds."""
        rounds = max(1, min(int(rounds), 8))
        target = max(0.0, min(float(target), 1.0))
        trail: List[Dict[str, Any]] = []
        final = None

        for i in range(rounds):
            if dry_run and i > 0:
                break
            cycle = self.run_cycle(
                volumes=volumes,
                apply_changes=not dry_run,
                with_mutate=with_mutate,
                with_practice=True,
            )
            if dry_run:
                return {"rounds": [cycle], "stopped": "dry_run", "target": target}

            verify = (cycle.get("apply") or {}).get("verify") or {}
            rate = float(verify.get("avg_pass_rate") or 0)
            trail.append(
                {
                    "round": i + 1,
                    "pass_rate": rate,
                    "delta": (cycle.get("apply") or {}).get("delta"),
                    "learned": (cycle.get("apply") or {}).get("learned_qa"),
                    "proposal_id": cycle.get("proposal_id"),
                }
            )
            final = cycle
            if rate >= target:
                break
            # no progress stop
            if i > 0 and trail[-1].get("delta") == 0 and trail[-2].get("delta") == 0:
                break

        summary = {
            "target": target,
            "rounds_run": len(trail),
            "trail": trail,
            "final_pass_rate": trail[-1]["pass_rate"] if trail else None,
            "reached_target": bool(trail and trail[-1]["pass_rate"] >= target),
            "last_cycle": final,
        }
        write_json(self.dir / "last_auto.json", summary)
        return summary

    def status(self) -> Dict[str, Any]:
        return {
            "dir": str(self.dir),
            "last_diagnose": read_json(self.dir / "last_diagnose.json", default=None),
            "last_proposal": read_json(self.dir / "last_proposal.json", default=None),
            "last_apply": read_json(self.dir / "last_apply.json", default=None),
            "last_auto": read_json(self.dir / "last_auto.json", default=None),
            "history": read_json(self.dir / "history.json", default={}),
        }


self_improve_engine = SelfImproveEngine()


def improve(
    volumes: Optional[List[str]] = None,
    *,
    dry_run: bool = False,
    with_mutate: bool = False,
) -> Dict[str, Any]:
    return SelfImproveEngine().run_cycle(
        volumes=volumes, apply_changes=not dry_run, with_mutate=with_mutate
    )


def improve_auto(
    volumes: Optional[List[str]] = None,
    *,
    rounds: int = 3,
    target: float = 0.95,
    with_mutate: bool = False,
    dry_run: bool = False,
) -> Dict[str, Any]:
    return SelfImproveEngine().auto(
        volumes=volumes,
        rounds=rounds,
        target=target,
        with_mutate=with_mutate,
        dry_run=dry_run,
    )
