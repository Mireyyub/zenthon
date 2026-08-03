"""Leon CLI – think/reason via ReasoningEngine (Faza 3)."""

import argparse
import sys
import json

from core.logger import logger
from core.kernel import kernel
from core.config import config


def parse_args():
    parser = argparse.ArgumentParser(
        description="Leon AI Platform CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m interfaces.cli.main_cli reason "Daş mövcuddurmu?"
  python -m interfaces.cli.main_cli think "Obyekt nədir?"
  python -m interfaces.cli.main_cli eval 01
  python -m interfaces.cli.main_cli teach-volume 01
        """,
    )
    sub = parser.add_subparsers(dest="command")

    start_p = sub.add_parser("start")
    start_p.add_argument("--bootstrap", action="store_true")
    start_p.add_argument("--volume", default="01")
    start_p.add_argument("--no-llm-check", action="store_true")
    start_p.add_argument("--json", action="store_true")

    sub.add_parser("smoke")
    save_p = sub.add_parser("save")
    save_p.add_argument("--name", default="leon")
    save_p.add_argument("--json", action="store_true")
    sub.add_parser("load")

    eval_p = sub.add_parser("eval")
    eval_p.add_argument("volume_id", nargs="?", default="01")
    eval_p.add_argument("--no-teach", action="store_true")
    eval_p.add_argument("--json", action="store_true")

    reason_p = sub.add_parser("reason", help="Vahid ReasoningEngine")
    reason_p.add_argument("query", type=str)
    reason_p.add_argument("--strategy", default="auto")
    reason_p.add_argument("--goal", default=None)
    reason_p.add_argument("--no-brain", action="store_true")
    reason_p.add_argument("--json", action="store_true")

    think_p = sub.add_parser("think")
    think_p.add_argument("query", type=str)
    think_p.add_argument("--mode", default="auto", choices=["auto", "cot", "tot", "sot"])
    think_p.add_argument("--goal", default=None)
    think_p.add_argument("--agent", default=None)
    think_p.add_argument("--json", action="store_true")

    agent_p = sub.add_parser("agent")
    agent_p.add_argument(
        "type",
        choices=["coding", "research", "executor", "vision", "voice", "react", "pev", "reflexion"],
    )
    agent_p.add_argument("task", type=str)
    agent_p.add_argument("--json", action="store_true")

    teach_p = sub.add_parser("teach")
    teach_p.add_argument("lesson_id", nargs="?", default="000001")
    teach_p.add_argument("--volume", default=None)
    teach_p.add_argument("--json", action="store_true")

    tv = sub.add_parser("teach-volume")
    tv.add_argument("volume_id", nargs="?", default="01")
    tv.add_argument("--json", action="store_true")

    sub.add_parser("volumes")
    sub.add_parser("lessons")
    sub.add_parser("status")
    sub.add_parser("info")
    sub.add_parser("llm-check")

    return parser.parse_args()


def _print_reason(result: dict):
    print(f"Answer     : {result.get('answer') or result.get('conclusion')}")
    print(f"Confidence : {result.get('confidence')} ({result.get('confidence_label')})")
    print(f"Source     : {result.get('source')}")
    print(f"Validation : {result.get('validation')}")
    if result.get("conflict"):
        print(f"Conflict   : {result.get('conflict')}")
    print(f"Trace ID   : {result.get('trace_id')}")
    print(f"LLM used   : {result.get('llm_used')}")
    dec = result.get("decision") or {}
    print(f"Decision   : {dec.get('action')} (risk={dec.get('risk')})")
    ev = result.get("evidence") or []
    if ev:
        print("Evidence:")
        for e in ev[:8]:
            print(f"  - [{e.get('kind')}] {e.get('content')[:120]}")


class CLIController:
    def cmd_start(self, args):
        from core.bootstrap import start_leon

        report = start_leon(
            bootstrap_curriculum=args.bootstrap,
            volume_id=args.volume,
            check_llm=not args.no_llm_check,
            load_persisted=True,
        )
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
            return
        for step in report.get("steps") or []:
            print(f"[{'OK' if step.get('ok') else 'FAIL'}] {step.get('step')}")

    def cmd_smoke(self):
        from core.bootstrap import smoke_test

        report = smoke_test()
        print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
        print("SMOKE:", "PASS" if report.get("overall_ok") else "FAIL")
        if not report.get("overall_ok"):
            sys.exit(1)

    def cmd_save(self, args):
        from core.bootstrap import save_state

        report = save_state(name=args.name)
        print(json.dumps(report, ensure_ascii=False, indent=2, default=str) if args.json else report)

    def cmd_load(self):
        from core.bootstrap import load_state

        print(json.dumps(load_state(), ensure_ascii=False, indent=2, default=str))

    def cmd_eval(self, args):
        from evaluation.runner import evaluate_curriculum

        report = evaluate_curriculum(args.volume_id, teach_first=not args.no_teach)
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
            return
        print(f"Pass rate : {report.get('pass_rate')} ({report.get('passed')}/{report.get('total')})")

    def cmd_reason(self, args):
        from brain.reasoning.engine import reasoning_engine

        result = reasoning_engine.reason(
            args.query,
            strategy=args.strategy,
            goal=args.goal,
            use_brain=not args.no_brain,
        )
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
            return
        _print_reason(result)

    def cmd_think(self, args):
        from brain.orchestrator import BrainOrchestrator

        orch = BrainOrchestrator(brain_name=config.ai_name)
        result = orch.run(
            args.query,
            goal=args.goal,
            reasoning_mode=args.mode,
            agent_type=args.agent,
        )
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
            return
        _print_reason(result)

    def cmd_agent(self, args):
        from agents.manager import agent_manager

        agent = agent_manager.create(args.type)
        res = agent_manager.run(agent.id, args.task)
        print(f"Success: {res.success}\n{res.output}")

    def cmd_teach(self, args):
        from curriculum import CurriculumEngine
        from core.bootstrap import save_state

        eng = CurriculumEngine()
        report = eng.teach(args.lesson_id, volume_id=getattr(args, "volume", None))
        try:
            save_state("after_teach")
        except Exception:
            pass
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
            return
        st = report.get("self_test") or {}
        print(f"{report.get('name')}: {st.get('passed')}/{st.get('total')}")

    def cmd_teach_volume(self, args):
        from curriculum import CurriculumEngine
        from core.bootstrap import save_state

        eng = CurriculumEngine()
        report = eng.teach_volume(args.volume_id)
        try:
            save_state("after_teach_volume")
        except Exception:
            pass
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
            return
        print(f"Lessons {report.get('lessons_passed')}/{report.get('lessons_total')}")
        ev = report.get("eval") or {}
        print(f"Eval {ev.get('pass_rate')}")

    def cmd_volumes(self):
        from curriculum import CurriculumEngine, load_volume

        eng = CurriculumEngine()
        for vid in eng.list_volumes():
            try:
                m = load_volume(vid)
                print(f"{m.get('volume')} | {m.get('name')}")
            except Exception as e:
                print(vid, e)

    def cmd_lessons(self):
        from curriculum import CurriculumEngine

        print(CurriculumEngine().list_available())

    def cmd_status(self):
        from core.bootstrap import leon_status

        print(json.dumps(leon_status(), ensure_ascii=False, indent=2, default=str))

    def cmd_info(self):
        kernel.initialize()
        print(f"{config.ai_name} | {config.path.leon_dir}")

    def cmd_llm_check(self):
        from brain.llm.client import get_llm_client

        print(json.dumps(get_llm_client(force_new=True).health_check(), ensure_ascii=False, indent=2))


def main():
    args = parse_args()
    ctrl = CLIController()
    try:
        cmd = args.command
        mapping = {
            "start": lambda: ctrl.cmd_start(args),
            "smoke": ctrl.cmd_smoke,
            "save": lambda: ctrl.cmd_save(args),
            "load": ctrl.cmd_load,
            "eval": lambda: ctrl.cmd_eval(args),
            "reason": lambda: ctrl.cmd_reason(args),
            "think": lambda: ctrl.cmd_think(args),
            "agent": lambda: ctrl.cmd_agent(args),
            "teach": lambda: ctrl.cmd_teach(args),
            "teach-volume": lambda: ctrl.cmd_teach_volume(args),
            "volumes": ctrl.cmd_volumes,
            "lessons": ctrl.cmd_lessons,
            "status": ctrl.cmd_status,
            "info": ctrl.cmd_info,
            "llm-check": ctrl.cmd_llm_check,
        }
        if cmd not in mapping:
            print("Leon CLI – --help")
            sys.exit(1)
        mapping[cmd]()
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
