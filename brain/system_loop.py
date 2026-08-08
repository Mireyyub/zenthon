"""
Leon system-wide health + improvement orchestration.

Brings together:
  body map · curriculum eval · self-improve · mutate status · smoke
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.persistence import write_json


def _dir() -> Path:
    try:
        from core.config import config

        d = Path(config.path.leon_dir) / "system"
    except Exception:
        d = Path("data/leon/system")
    d.mkdir(parents=True, exist_ok=True)
    return d


class SystemLoop:
    def status(self) -> Dict[str, Any]:
        from brain.policy_bind import bind_mutate_policy

        bind_mutate_policy()
        out: Dict[str, Any] = {
            "identity": "Leon",
            "at": datetime.now().isoformat(),
            "layers": {},
        }

        # body
        try:
            from brain.self_view import SelfView

            out["layers"]["body"] = SelfView().body()
        except Exception as e:
            out["layers"]["body"] = {"ok": False, "error": str(e)}

        # bootstrap status
        try:
            from core.bootstrap import leon_status

            out["layers"]["runtime"] = leon_status()
        except Exception as e:
            out["layers"]["runtime"] = {"ok": False, "error": str(e)}

        # improve diagnose (light)
        try:
            from brain.self_improve import SelfImproveEngine

            d = SelfImproveEngine().diagnose(volumes=["01", "02"])
            out["layers"]["curriculum"] = {
                "severity": d.get("severity"),
                "avg_pass_rate": d.get("avg_pass_rate"),
                "weak_cases": len(d.get("weak_cases") or []),
                "topics": d.get("topic_counts"),
            }
        except Exception as e:
            out["layers"]["curriculum"] = {"ok": False, "error": str(e)}

        # mutate
        try:
            from brain.self_mutate import SelfMutateEngine

            out["layers"]["mutate"] = SelfMutateEngine().status()
        except Exception as e:
            out["layers"]["mutate"] = {"ok": False, "error": str(e)}

        # security
        try:
            from security.gate import safe_tool_call

            out["layers"]["security"] = {"gate": "present", "ok": True}
        except Exception as e:
            out["layers"]["security"] = {"ok": False, "error": str(e)}

        # score
        ok_bits = []
        cur = out["layers"].get("curriculum") or {}
        if isinstance(cur.get("avg_pass_rate"), (int, float)):
            ok_bits.append(float(cur["avg_pass_rate"]))
        body = out["layers"].get("body") or {}
        if body.get("summary"):
            ok_bits.append(1.0)
        mut = out["layers"].get("mutate") or {}
        if "enabled" in mut:
            ok_bits.append(0.8 if mut.get("enabled") else 0.6)
        out["health_score"] = round(sum(ok_bits) / max(len(ok_bits), 1), 3)
        out["ok"] = out["health_score"] >= 0.5

        write_json(_dir() / "last_status.json", out)
        return out

    def improve(
        self,
        *,
        volumes: Optional[List[str]] = None,
        rounds: int = 2,
        target: float = 0.95,
        with_mutate: bool = False,
        with_codegen: bool = False,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Full system improve: diagnose body + curriculum cycle + optional codegen."""
        from brain.policy_bind import bind_mutate_policy

        bind_mutate_policy()
        before = self.status()

        from brain.self_improve import improve_auto

        auto = improve_auto(
            volumes=volumes or ["01", "02"],
            rounds=rounds,
            target=target,
            with_mutate=with_mutate,
            with_codegen=with_codegen,
            dry_run=dry_run,
        )

        after = None if dry_run else self.status()
        report = {
            "at": datetime.now().isoformat(),
            "before": {
                "health_score": before.get("health_score"),
                "curriculum": before.get("layers", {}).get("curriculum"),
            },
            "auto": auto,
            "after": {
                "health_score": (after or {}).get("health_score"),
                "curriculum": (after or {}).get("layers", {}).get("curriculum"),
            }
            if after
            else None,
            "options": {
                "with_mutate": with_mutate,
                "with_codegen": with_codegen,
                "dry_run": dry_run,
            },
        }
        write_json(_dir() / "last_improve.json", report)
        return report

    def smoke(self) -> Dict[str, Any]:
        from core.bootstrap import smoke_test

        r = smoke_test()
        # extend with self_view + improve dry
        extra = {}
        try:
            from brain.self_view import SelfView

            extra["body_ok"] = bool(SelfView().body().get("summary"))
        except Exception as e:
            extra["body_ok"] = False
            extra["body_error"] = str(e)
        try:
            from brain.policy_bind import bind_mutate_policy

            extra["policy_bound"] = bind_mutate_policy()
        except Exception:
            extra["policy_bound"] = False
        r["system_extra"] = extra
        r["overall_ok"] = bool(r.get("overall_ok")) and bool(extra.get("body_ok"))
        write_json(_dir() / "last_smoke.json", r)
        return r


system_loop = SystemLoop()
