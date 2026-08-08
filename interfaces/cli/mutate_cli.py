"""CLI helpers for self-mutation v2."""

from __future__ import annotations

import json
from typing import Any


def run_mutate(args: Any) -> None:
    from brain.self_mutate import SelfMutateEngine, STRATEGIES

    eng = SelfMutateEngine()
    cmd = getattr(args, "mut_cmd", None)

    if cmd == "status" or cmd is None:
        print(json.dumps(eng.status(), ensure_ascii=False, indent=2, default=str))
        return

    if cmd == "propose":
        if getattr(args, "strategy", None):
            out = eng.propose_strategy(
                args.strategy,
                goal=getattr(args, "goal", "") or "",
                path=getattr(args, "path", None),
            )
        elif getattr(args, "goal", None):
            out = eng.propose_from_goal(
                args.goal,
                path=getattr(args, "path", None),
                candidates=int(getattr(args, "candidates", 3) or 3),
                strategy=getattr(args, "strategy", None),
            )
        else:
            if not getattr(args, "path", None):
                print(
                    json.dumps(
                        {
                            "ok": False,
                            "error": "--path or --goal or --strategy required",
                            "strategies": list(STRATEGIES),
                        }
                    )
                )
                return
            out = eng.propose(
                args.path,
                mode=args.mode,
                old=args.old or "",
                new=args.new or "",
                content=args.content or "",
                reason=args.reason or "",
                strategy=getattr(args, "strategy", "") or "",
            )
        print(json.dumps(out, ensure_ascii=False, indent=2, default=str))
        return

    if cmd == "smart":
        goal = getattr(args, "goal", None) or ""
        out = eng.auto_cycle(
            goal=goal or None,
            apply_best=bool(getattr(args, "apply", False)),
            from_diagnose=not bool(getattr(args, "no_diagnose", False)),
        )
        print(json.dumps(out, ensure_ascii=False, indent=2, default=str))
        return

    if cmd == "evolve":
        out = eng.evolve(
            rounds=int(getattr(args, "rounds", 2) or 2),
            apply_changes=bool(getattr(args, "apply", False)),
            goal=getattr(args, "goal", None),
            min_quality=float(getattr(args, "min_quality", 40.0) or 40.0),
        )
        print(json.dumps(out, ensure_ascii=False, indent=2, default=str))
        return

    if cmd == "diagnose":
        out = eng.propose_from_diagnosis()
        print(json.dumps(out, ensure_ascii=False, indent=2, default=str))
        return

    if cmd == "route":
        out = eng.route_goal(getattr(args, "goal", "") or "")
        print(json.dumps(out, ensure_ascii=False, indent=2, default=str))
        return

    if cmd == "list":
        out = eng.list_proposals(limit=int(getattr(args, "limit", 20) or 20))
        print(json.dumps(out, ensure_ascii=False, indent=2, default=str))
        return

    if cmd == "strategies":
        print(json.dumps({"strategies": list(STRATEGIES)}, ensure_ascii=False, indent=2))
        return

    if cmd == "apply":
        out = eng.apply(
            getattr(args, "proposal_id", None),
            run_smoke=not getattr(args, "no_smoke", False),
        )
        print(json.dumps(out, ensure_ascii=False, indent=2, default=str))
        return

    if cmd == "rollback":
        out = eng.rollback(args.mutation_id)
        print(json.dumps(out, ensure_ascii=False, indent=2, default=str))
        return

    print("mutate status|propose|smart|evolve|diagnose|route|list|strategies|apply|rollback")
