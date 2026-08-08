"""CLI: transfer eval + human suite."""

from __future__ import annotations

import json
from typing import Any


def run_eval_ext(args: Any) -> None:
    cmd = getattr(args, "ev_cmd", None)
    if cmd == "transfer":
        from evaluation.transfer import transfer_eval

        sources = [x.strip() for x in (getattr(args, "sources", "01,02") or "01,02").split(",") if x.strip()]
        out = transfer_eval(
            source_volumes=sources,
            target_volume=getattr(args, "target", "03") or "03",
            teach_source=not bool(getattr(args, "no_teach_source", False)),
            teach_target_after=not bool(getattr(args, "no_teach_target", False)),
        )
        print(json.dumps(out, ensure_ascii=False, indent=2, default=str))
        return
    if cmd == "human":
        from evaluation.human_suite import run_model_answers, score_summary

        if getattr(args, "summary", False):
            print(json.dumps(score_summary(), ensure_ascii=False, indent=2))
            return
        out = run_model_answers()
        print(json.dumps({"n": out.get("n"), "path_hint": "data/leon/eval/human/human_package.json", "cases": [
            {"id": c["id"], "answer": c.get("model_answer"), "conf": c.get("confidence")}
            for c in (out.get("cases") or [])
        ]}, ensure_ascii=False, indent=2))
        return
    if cmd == "long":
        from brain.planning import long_horizon_plan, Planner

        vols = [x.strip() for x in (getattr(args, "volumes", "01,02,03") or "01,02,03").split(",") if x.strip()]
        plan = long_horizon_plan(volumes=vols, transfer_target=getattr(args, "target", "03") or "03")
        if getattr(args, "run", False):
            report = Planner().run(plan.id)
            print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
        else:
            print(json.dumps({"plan_id": plan.id, "goal": plan.goal, "tasks": len(plan.tasks)}, ensure_ascii=False, indent=2))
        return
    print("eval-ext transfer|human|long")
