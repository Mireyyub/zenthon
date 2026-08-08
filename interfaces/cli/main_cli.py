"""Leon CLI – cognitive platform entry."""

from __future__ import annotations

import argparse
import json
import sys

from core.logger import logger
from core.config import config


def parse_args():
    p = argparse.ArgumentParser(description="Leon AI Platform CLI")
    sub = p.add_subparsers(dest="command")

    sp = sub.add_parser("start")
    sp.add_argument("--bootstrap", action="store_true")
    sp.add_argument("--volume", default="01")
    sp.add_argument("--no-llm-check", action="store_true")
    sp.add_argument("--json", action="store_true")

    sub.add_parser("smoke")
    sub.add_parser("health")
    sub.add_parser("status")
    sub.add_parser("info")
    sub.add_parser("llm-check")
    sub.add_parser("volumes")
    sub.add_parser("lessons")
    sub.add_parser("load")
    sv = sub.add_parser("save")
    sv.add_argument("--name", default="leon")

    ev = sub.add_parser("eval")
    ev.add_argument("volume_id", nargs="?", default="01")
    ev.add_argument("--no-teach", action="store_true")
    ev.add_argument("--json", action="store_true")

    rp = sub.add_parser("reason")
    rp.add_argument("query")
    rp.add_argument("--strategy", default="auto")
    rp.add_argument("--goal", default=None)
    rp.add_argument("--no-brain", action="store_true")
    rp.add_argument("--json", action="store_true")

    tp = sub.add_parser("think")
    tp.add_argument("query")
    tp.add_argument("--mode", default="auto", choices=["auto", "cot", "tot", "sot"])
    tp.add_argument("--goal", default=None)
    tp.add_argument("--agent", default=None)
    tp.add_argument("--experimental", action="store_true")
    tp.add_argument("--json", action="store_true")

    cyc = sub.add_parser("cycle", help="PODALR cognitive cycle")
    cyc.add_argument("query")
    cyc.add_argument("--goal", default=None)
    cyc.add_argument("--image", default=None)
    cyc.add_argument("--audio", default=None)
    cyc.add_argument("--agent", default=None)
    cyc.add_argument("--experimental", action="store_true")
    cyc.add_argument("--no-learn", action="store_true")
    cyc.add_argument("--no-reflect", action="store_true")
    cyc.add_argument("--json", action="store_true")

    crew = sub.add_parser("crew", help="Multi-agent crew")
    crew.add_argument("goal", nargs="?", default="analyze")
    crew.add_argument("--mode", default="sequential", choices=["sequential", "parallel", "debate"])
    crew.add_argument("--agents", default="react,coding")
    crew.add_argument("--research", action="store_true")
    crew.add_argument("--image", default=None)

    audio = sub.add_parser("audio", help="Speech / audio")
    audio_sub = audio.add_subparsers(dest="audio_cmd")
    audio_sub.add_parser("status")
    ai = audio_sub.add_parser("info")
    ai.add_argument("path")
    astt = audio_sub.add_parser("stt")
    astt.add_argument("path")
    atts = audio_sub.add_parser("tts")
    atts.add_argument("text")
    atts.add_argument("--out", default=None)
    audio_sub.add_parser("tone")

    eext = sub.add_parser("eval-ext", help="Transfer / human / long-horizon")
    eext_sub = eext.add_subparsers(dest="ev_cmd")
    et = eext_sub.add_parser("transfer")
    et.add_argument("--sources", default="01,02")
    et.add_argument("--target", default="03")
    et.add_argument("--no-teach-source", action="store_true")
    et.add_argument("--no-teach-target", action="store_true")
    eh = eext_sub.add_parser("human")
    eh.add_argument("--summary", action="store_true")
    el = eext_sub.add_parser("long")
    el.add_argument("--volumes", default="01,02,03")
    el.add_argument("--target", default="03")
    el.add_argument("--run", action="store_true")

    teach = sub.add_parser("teach")
    teach.add_argument("lesson_id", nargs="?", default="000001")
    teach.add_argument("--volume", default=None)
    teach.add_argument("--json", action="store_true")
    tv = sub.add_parser("teach-volume")
    tv.add_argument("volume_id", nargs="?", default="01")
    tv.add_argument("--json", action="store_true")

    imp = sub.add_parser("improve")
    imp_sub = imp.add_subparsers(dest="imp_cmd")
    idg = imp_sub.add_parser("diagnose")
    idg.add_argument("--volumes", default="01,02")
    irun = imp_sub.add_parser("run")
    irun.add_argument("--volumes", default="01,02")
    irun.add_argument("--dry-run", action="store_true")
    irun.add_argument("--with-mutate", action="store_true")
    irun.add_argument("--with-codegen", action="store_true")
    iauto = imp_sub.add_parser("auto")
    iauto.add_argument("--volumes", default="01,02")
    iauto.add_argument("--rounds", type=int, default=3)
    iauto.add_argument("--target", type=float, default=0.95)
    iauto.add_argument("--with-mutate", action="store_true")
    iauto.add_argument("--with-codegen", action="store_true")
    iauto.add_argument("--dry-run", action="store_true")
    imp_sub.add_parser("status")

    for name, help_ in (
        ("mutate", "Controlled mutation"),
        ("self", "Body awareness"),
        ("system", "System status"),
        ("image", "Multimodal"),
        ("omniverse", "Omniverse bridge"),
        ("plan", "Planner"),
        ("agent", "Agents"),
        ("retrieve", "Retrieve"),
        ("quarantine", "Quarantine"),
    ):
        sub.add_parser(name, help=help_)

    return p.parse_args()


def _print_reason(result: dict):
    print(f"Answer     : {result.get('answer') or result.get('conclusion')}")
    print(f"Confidence : {result.get('confidence')} ({result.get('confidence_label')})")
    print(f"Source     : {result.get('source')}")
    print(f"Trace ID   : {result.get('trace_id')}")


def _vols(s: str):
    return [v.strip() for v in (s or "01").split(",") if v.strip()]


def main():
    args = parse_args()
    cmd = args.command
    try:
        if cmd == "start":
            from core.bootstrap import start_leon

            report = start_leon(
                bootstrap_curriculum=args.bootstrap,
                volume_id=args.volume,
                check_llm=not args.no_llm_check,
                load_persisted=True,
            )
            print(json.dumps(report, ensure_ascii=False, indent=2, default=str) if args.json else report.get("ok"))
            return
        if cmd == "smoke":
            from core.bootstrap import smoke_test

            print(json.dumps(smoke_test(), ensure_ascii=False, indent=2, default=str))
            return
        if cmd == "health":
            from interfaces.api.health import health_report

            print(json.dumps(health_report(), ensure_ascii=False, indent=2, default=str))
            return
        if cmd == "status":
            from core.bootstrap import leon_status

            print(json.dumps(leon_status(), ensure_ascii=False, indent=2, default=str))
            return
        if cmd == "info":
            print(f"{config.ai_name} | {config.path.leon_dir}")
            return
        if cmd == "llm-check":
            from brain.llm.client import get_llm_client

            print(json.dumps(get_llm_client(force_new=True).health_check(), ensure_ascii=False, indent=2))
            return
        if cmd == "save":
            from core.bootstrap import save_state

            print(save_state(name=args.name))
            return
        if cmd == "load":
            from core.bootstrap import load_state

            print(json.dumps(load_state(), ensure_ascii=False, indent=2, default=str))
            return
        if cmd == "volumes":
            from curriculum import CurriculumEngine, load_volume

            for vid in CurriculumEngine().list_volumes():
                try:
                    m = load_volume(vid)
                    print(f"{m.get('volume')} | {m.get('name')}")
                except Exception as e:
                    print(vid, e)
            return
        if cmd == "lessons":
            from curriculum import CurriculumEngine

            print(CurriculumEngine().list_available())
            return
        if cmd == "eval":
            from evaluation.runner import evaluate_curriculum

            report = evaluate_curriculum(args.volume_id, teach_first=not args.no_teach)
            print(json.dumps(report, ensure_ascii=False, indent=2, default=str) if args.json else f"Pass rate : {report.get('pass_rate')}")
            return
        if cmd == "reason":
            from brain.reasoning.engine import reasoning_engine

            result = reasoning_engine.reason(
                args.query, strategy=args.strategy, goal=args.goal, use_brain=not args.no_brain
            )
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
            else:
                _print_reason(result)
            return
        if cmd == "think":
            from brain.orchestrator import BrainOrchestrator

            result = BrainOrchestrator(brain_name=config.ai_name).run(
                args.query,
                goal=args.goal,
                reasoning_mode=args.mode,
                agent_type=args.agent,
                allow_experimental_agent=args.experimental,
            )
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
            else:
                _print_reason(result)
            return
        if cmd == "cycle":
            from interfaces.cli.cycle_cli import run_cycle

            run_cycle(args)
            return
        if cmd == "crew":
            from interfaces.cli.crew_cli import run_crew_cmd

            run_crew_cmd(args)
            return
        if cmd == "audio":
            from interfaces.cli.crew_cli import run_audio_cmd

            run_audio_cmd(args)
            return
        if cmd == "eval-ext":
            from interfaces.cli.eval_ext_cli import run_eval_ext

            run_eval_ext(args)
            return
        if cmd == "teach":
            from curriculum import CurriculumEngine
            from core.bootstrap import save_state

            report = CurriculumEngine().teach(args.lesson_id, volume_id=getattr(args, "volume", None))
            try:
                save_state("after_teach")
            except Exception:
                pass
            st = report.get("self_test") or {}
            print(json.dumps(report, ensure_ascii=False, indent=2, default=str) if args.json else f"{report.get('name')}: {st.get('passed')}/{st.get('total')}")
            return
        if cmd == "teach-volume":
            from curriculum import CurriculumEngine
            from core.bootstrap import save_state

            report = CurriculumEngine().teach_volume(args.volume_id)
            try:
                save_state("after_teach_volume")
            except Exception:
                pass
            print(json.dumps(report, ensure_ascii=False, indent=2, default=str) if args.json else f"Lessons {report.get('lessons_passed')}/{report.get('lessons_total')}")
            return
        if cmd == "improve":
            from brain.self_improve import SelfImproveEngine, improve, improve_auto

            eng = SelfImproveEngine()
            ic = args.imp_cmd
            if ic == "status" or ic is None:
                print(json.dumps(eng.status(), ensure_ascii=False, indent=2, default=str))
            elif ic == "diagnose":
                print(json.dumps(eng.diagnose(volumes=_vols(args.volumes)), ensure_ascii=False, indent=2, default=str))
            elif ic == "run":
                print(json.dumps(improve(volumes=_vols(args.volumes), dry_run=args.dry_run, with_mutate=bool(getattr(args, "with_mutate", False)), with_codegen=bool(getattr(args, "with_codegen", False))), ensure_ascii=False, indent=2, default=str))
            elif ic == "auto":
                print(json.dumps(improve_auto(volumes=_vols(args.volumes), rounds=args.rounds, target=args.target, with_mutate=bool(getattr(args, "with_mutate", False)), with_codegen=bool(getattr(args, "with_codegen", False)), dry_run=args.dry_run), ensure_ascii=False, indent=2, default=str))
            else:
                print("improve diagnose|run|auto|status")
            return
        if cmd == "mutate":
            from brain.self_mutate import SelfMutateEngine

            print(json.dumps(SelfMutateEngine().status(), ensure_ascii=False, indent=2, default=str))
            return
        if cmd == "self":
            from brain.self_view import SelfView

            print(json.dumps(SelfView().body(), ensure_ascii=False, indent=2, default=str))
            return
        if cmd == "system":
            from brain.system_loop import SystemLoop

            print(json.dumps(SystemLoop().status(), ensure_ascii=False, indent=2, default=str))
            return
        if cmd == "plan":
            from brain.planning import long_horizon_plan

            plan = long_horizon_plan()
            print(json.dumps({"plan_id": plan.id, "goal": plan.goal, "tasks": len(plan.tasks)}, ensure_ascii=False, indent=2))
            return
        if cmd == "retrieve":
            from memory.retrieve import retrieve

            print(json.dumps(retrieve("obyekt", top_k=5), ensure_ascii=False, indent=2, default=str))
            return
        if cmd in ("image", "omniverse", "agent", "quarantine"):
            print(f"{cmd}: detailed subcommands in dedicated modules")
            return
        print("Leon CLI – start|reason|think|cycle|crew|audio|eval|eval-ext|teach-volume|improve|system")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
