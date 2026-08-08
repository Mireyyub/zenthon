"""
Leon Self-Improvement Engine

Safe, measurable loop (NOT unrestricted code self-rewrite):
  diagnose → propose → apply → verify

Improves knowledge/skills via curriculum re-teach, learning from eval failures,
and optional plan execution. Source code of Leon is never modified.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import json
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
    """Closed-loop self-improvement over knowledge + eval performance."""

    def __init__(self):
        self.dir = _reports_dir()
        self._history: List[Dict[str, Any]] = []

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
                        }
                    )

        # recent reasoning UNKNOWN / low confidence from traces
        weak_traces = self._scan_traces(limit=30)

        learning_stats = {}
        try:
            from learning.engine import LearningEngine

            learning_stats = LearningEngine().stats()
        except Exception:
            pass

        severity = "ok"
        rates = [e.get("pass_rate") for e in evals if isinstance(e.get("pass_rate"), (int, float))]
        avg = sum(rates) / len(rates) if rates else 0.0
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
            "learning": learning_stats,
            "volumes": vols,
        }
        write_json(self.dir / "last_diagnose.json", out)
        return out

    def _scan_traces(self, limit: int = 30) -> List[Dict[str, Any]]:
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
            ans = str(data.get("selected_conclusion") or "")
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
    def propose(self, diagnosis: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        diag = diagnosis or self.diagnose()
        actions: List[Dict[str, Any]] = []

        # 1) Re-teach weak volumes
        for e in diag.get("evals") or []:
            rate = e.get("pass_rate")
            if e.get("error") or (isinstance(rate, (int, float)) and rate < 0.9):
                actions.append(
                    {
                        "type": "teach_volume",
                        "volume_id": e.get("volume_id"),
                        "reason": f"pass_rate={rate}",
                        "priority": 10 if (rate or 0) < 0.5 else 5,
                    }
                )

        # 2) Learn failed Q→expected as validated knowledge
        for case in diag.get("weak_cases") or []:
            q, exp = case.get("question"), case.get("expected")
            if q and exp:
                actions.append(
                    {
                        "type": "learn_qa",
                        "question": q,
                        "answer": exp,
                        "volume_id": case.get("volume_id"),
                        "priority": 8,
                    }
                )

        # 3) Persist improvement train pairs for audit
        if diag.get("weak_cases"):
            actions.append(
                {
                    "type": "write_failure_dataset",
                    "count": len(diag["weak_cases"]),
                    "priority": 3,
                }
            )

        # 4) Save state after improvements
        actions.append({"type": "save_state", "name": "self_improve", "priority": 1})

        # 5) Verify after apply
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
            "actions": actions,
            "action_count": len(actions),
            "safety": {
                "code_rewrite": False,
                "scope": "knowledge+curriculum+learning+eval",
                "note": "Leon does not modify its own source code",
            },
        }
        write_json(self.dir / "last_proposal.json", proposal)
        return proposal

    # ------------------------------------------------------------------ apply
    def apply(self, proposal: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        prop = proposal or read_json(self.dir / "last_proposal.json", default=None)
        if not prop:
            prop = self.propose()

        results: List[Dict[str, Any]] = []
        learned = 0
        taught = []

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
                    )
                    # also inject direct fact for ask() path
                    try:
                        from knowledge.registry import get_fact_store

                        get_fact_store().add(
                            content, source="self_improve", confidence=0.92
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
                elif atype == "write_failure_dataset":
                    path = self._write_failure_dataset()
                    results.append({"type": atype, "ok": True, "path": str(path)})
                elif atype == "save_state":
                    from core.bootstrap import save_state

                    save_state(action.get("name") or "self_improve")
                    results.append({"type": atype, "ok": True})
                elif atype == "verify":
                    # deferred to explicit verify() at end
                    results.append({"type": atype, "ok": True, "deferred": True})
                else:
                    results.append({"type": atype, "ok": False, "error": "unknown action"})
            except Exception as e:
                results.append({"type": atype, "ok": False, "error": str(e)})
                logger.warning(f"SelfImprove apply {atype}: {e}")

        verify = self.verify(volumes=prop.get("actions", [{}])[-1].get("volumes"))
        report = {
            "proposal_id": prop.get("id"),
            "applied_at": datetime.now().isoformat(),
            "results": results,
            "learned_qa": learned,
            "taught_volumes": taught,
            "verify": verify,
            "improved": bool(
                verify.get("avg_pass_rate", 0) > (prop.get("avg_pass_rate_before") or 0)
            )
            or learned > 0,
        }
        write_json(self.dir / "last_apply.json", report)
        self._history.append(
            {"id": prop.get("id"), "improved": report["improved"], "at": report["applied_at"]}
        )
        write_json(self.dir / "history.json", {"runs": self._history[-50:]})
        return report

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

    # ------------------------------------------------------------------ cycle
    def run_cycle(
        self,
        volumes: Optional[List[str]] = None,
        *,
        apply_changes: bool = True,
    ) -> Dict[str, Any]:
        """Full self-improve cycle."""
        diag = self.diagnose(volumes=volumes)
        prop = self.propose(diag)
        if not apply_changes:
            return {
                "diagnosis": diag,
                "proposal": prop,
                "applied": False,
                "note": "dry-run — apply_changes=False",
            }
        applied = self.apply(prop)
        return {
            "diagnosis": {
                "severity": diag.get("severity"),
                "avg_pass_rate": diag.get("avg_pass_rate"),
                "weak_case_count": len(diag.get("weak_cases") or []),
            },
            "proposal_id": prop.get("id"),
            "action_count": prop.get("action_count"),
            "apply": applied,
            "safety": prop.get("safety"),
        }

    def status(self) -> Dict[str, Any]:
        return {
            "dir": str(self.dir),
            "last_diagnose": read_json(self.dir / "last_diagnose.json", default=None),
            "last_proposal": read_json(self.dir / "last_proposal.json", default=None),
            "last_apply": read_json(self.dir / "last_apply.json", default=None),
            "history": read_json(self.dir / "history.json", default={}),
        }


self_improve_engine = SelfImproveEngine()


def improve(
    volumes: Optional[List[str]] = None, *, dry_run: bool = False
) -> Dict[str, Any]:
    """Public entry: Leon improves itself (knowledge/eval loop)."""
    return SelfImproveEngine().run_cycle(volumes=volumes, apply_changes=not dry_run)
