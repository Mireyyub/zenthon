"""Leon CLI – start / smoke / save / load / eval / curriculum."""

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
  python -m interfaces.cli.main_cli start --bootstrap
  python -m interfaces.cli.main_cli teach-volume 01
  python -m interfaces.cli.main_cli eval 01
  python -m interfaces.cli.main_cli save
  python -m interfaces.cli.main_cli smoke
        """,
    )
    sub = parser.add_subparsers(dest="command")

    start_p = sub.add_parser("start", help="Leon bootstrap")
    start_p.add_argument("--bootstrap", action="store_true")
    start_p.add_argument("--volume", default="01")
    start_p.add_argument("--no-llm-check", action="store_true")
    start_p.add_argument("--json", action="store_true")

    sub.add_parser("smoke", help="Smoke test")

    save_p = sub.add_parser("save", help="Diskə yaz")
    save_p.add_argument("--name", default="leon")
    save_p.add_argument("--json", action="store_true")

    sub.add_parser("load", help="Diskdən yüklə")

    eval_p = sub.add_parser("eval", help="Curriculum volume eval.jsonl")
    eval_p.add_argument("volume_id", nargs="?", default="01")
    eval_p.add_argument("--no-teach", action="store_true", help="teach etmədən yalnız eval")
    eval_p.add_argument("--json", action="store_true")

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
        print(f"AI: {config.ai_name}")
        for step in report.get("steps") or []:
            mark = "OK" if step.get("ok") else "FAIL"
            print(f"  [{mark}] {step.get('step')}")

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
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
            return
        print(f"Saved: {report.get('checkpoint_id')}")
        print(report.get("parts"))

    def cmd_load(self):
        from core.bootstrap import load_state

        print(json.dumps(load_state(), ensure_ascii=False, indent=2, default=str))

    def cmd_eval(self, args):
        from evaluation.runner import evaluate_curriculum

        report = evaluate_curriculum(args.volume_id, teach_first=not args.no_teach)
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
            return
        print(f"Volume    : {report.get('volume_id')}")
        print(f"Pass rate : {report.get('pass_rate')} ({report.get('passed')}/{report.get('total')})")
        for c in report.get("cases") or []:
            mark = "OK" if c.get("pass") else "FAIL"
            print(f"  [{mark}] {c.get('question')} → {c.get('got')} (expected {c.get('expected')})")

    def cmd_think(self, args):
        from brain.orchestrator import BrainOrchestrator

        orch = BrainOrchestrator(brain_name=config.ai_name)
        result = orch.run(args.query, goal=args.goal, reasoning_mode=args.mode, agent_type=args.agent)
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
            return
        print(f"Conclusion : {result.get('conclusion')}")
        print(f"Confidence : {result.get('confidence')}")

    def cmd_agent(self, args):
        from agents.manager import agent_manager

        agent = agent_manager.create(args.type)
        res = agent_manager.run(agent.id, args.task)
        print(f"Success : {res.success}\nOutput  : {res.output}")

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
        print(f"Volume: {report.get('name')} lessons {report.get('lessons_passed')}/{report.get('lessons_total')}")
        ev = report.get("eval") or {}
        print(f"Eval: {ev.get('pass_rate')} ({ev.get('passed')}/{ev.get('total')})")

    def cmd_volumes(self):
        from curriculum import CurriculumEngine, load_volume

        eng = CurriculumEngine()
        for vid in eng.list_volumes():
            try:
                meta = load_volume(vid)
                print(f"{meta.get('volume')} | {meta.get('name')} lessons={meta.get('lessons')}")
            except Exception as e:
                print(vid, e)

    def cmd_lessons(self):
        from curriculum import CurriculumEngine

        eng = CurriculumEngine()
        print(eng.list_available())

    def cmd_status(self):
        from core.bootstrap import leon_status

        print(json.dumps(leon_status(), ensure_ascii=False, indent=2, default=str))

    def cmd_info(self):
        kernel.initialize()
        print(f"{config.ai_name} | {config.path.leon_dir} | {config.llm.model}")

    def cmd_llm_check(self):
        from brain.llm.client import get_llm_client

        print(json.dumps(get_llm_client(force_new=True).health_check(), ensure_ascii=False, indent=2))


def main():
    args = parse_args()
    ctrl = CLIController()
    try:
        cmd = args.command
        if cmd == "start":
            ctrl.cmd_start(args)
        elif cmd == "smoke":
            ctrl.cmd_smoke()
        elif cmd == "save":
            ctrl.cmd_save(args)
        elif cmd == "load":
            ctrl.cmd_load()
        elif cmd == "eval":
            ctrl.cmd_eval(args)
        elif cmd == "think":
            ctrl.cmd_think(args)
        elif cmd == "agent":
            ctrl.cmd_agent(args)
        elif cmd == "teach":
            ctrl.cmd_teach(args)
        elif cmd == "teach-volume":
            ctrl.cmd_teach_volume(args)
        elif cmd == "volumes":
            ctrl.cmd_volumes()
        elif cmd == "lessons":
            ctrl.cmd_lessons()
        elif cmd == "status":
            ctrl.cmd_status()
        elif cmd == "info":
            ctrl.cmd_info()
        elif cmd == "llm-check":
            ctrl.cmd_llm_check()
        else:
            print("Leon CLI – --help")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
