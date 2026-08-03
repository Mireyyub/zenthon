"""
Leon CLI – start / smoke / save / load / think / curriculum.
"""

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
  python -m interfaces.cli.main_cli start
  python -m interfaces.cli.main_cli start --bootstrap
  python -m interfaces.cli.main_cli smoke
  python -m interfaces.cli.main_cli save
  python -m interfaces.cli.main_cli load
  python -m interfaces.cli.main_cli status
  python -m interfaces.cli.main_cli think "Obyekt nədir?"
  python -m interfaces.cli.main_cli teach-volume 01
        """,
    )
    sub = parser.add_subparsers(dest="command")

    start_p = sub.add_parser("start", help="Leon bootstrap")
    start_p.add_argument("--bootstrap", action="store_true")
    start_p.add_argument("--volume", default="01")
    start_p.add_argument("--no-llm-check", action="store_true")
    start_p.add_argument("--json", action="store_true")

    sub.add_parser("smoke", help="Faza 0+1 smoke test")

    save_p = sub.add_parser("save", help="Bütün bilikləri diskə yaz")
    save_p.add_argument("--name", default="leon")
    save_p.add_argument("--json", action="store_true")

    sub.add_parser("load", help="Diskdən bilikləri yüklə")

    think_p = sub.add_parser("think", help="ThinkingBrain")
    think_p.add_argument("query", type=str)
    think_p.add_argument("--mode", default="auto", choices=["auto", "cot", "tot", "sot"])
    think_p.add_argument("--goal", default=None)
    think_p.add_argument("--agent", default=None)
    think_p.add_argument("--json", action="store_true")

    agent_p = sub.add_parser("agent", help="Agent")
    agent_p.add_argument(
        "type",
        choices=["coding", "research", "executor", "vision", "voice", "react", "pev", "reflexion"],
    )
    agent_p.add_argument("task", type=str)
    agent_p.add_argument("--json", action="store_true")

    teach_p = sub.add_parser("teach", help="Tək dərs")
    teach_p.add_argument("lesson_id", nargs="?", default="000001")
    teach_p.add_argument("--volume", default=None)
    teach_p.add_argument("--json", action="store_true")

    tv = sub.add_parser("teach-volume", help="Cild")
    tv.add_argument("volume_id", nargs="?", default="01")
    tv.add_argument("--json", action="store_true")

    sub.add_parser("volumes")
    sub.add_parser("lessons")
    sub.add_parser("status")
    sub.add_parser("info")
    sub.add_parser("llm-check")

    train_p = sub.add_parser("train")
    train_p.add_argument("--model", required=True, choices=["linear_regression", "random_forest", "kmeans", "simple_nn"])
    train_p.add_argument("--data", required=True)
    train_p.add_argument("--target", required=True)
    train_p.add_argument("--test_size", type=float, default=0.2)
    train_p.add_argument("--epochs", type=int, default=10)
    train_p.add_argument("--batch_size", type=int, default=32)
    train_p.add_argument("--learning_rate", type=float, default=0.001)
    train_p.add_argument("--save_model", default=None)

    pred_p = sub.add_parser("predict")
    pred_p.add_argument("--model", required=True)
    pred_p.add_argument("--data", required=True)
    pred_p.add_argument("--output", default=None)

    sub.add_parser("list_models")

    return parser.parse_args()


class CLIController:
    def __init__(self):
        self.models = {}
        self.predictors = {}

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
        print(f"leon_dir: {config.path.leon_dir}")
        for step in report.get("steps") or []:
            mark = "OK" if step.get("ok") else "FAIL"
            extra = step.get("error") or ""
            print(f"  [{mark}] {step.get('step')} {extra}")
        if report.get("persisted"):
            print(f"  persisted: {report['persisted'].get('parts')}")
        for w in report.get("warnings") or []:
            print(f"  WARN: {w}")

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
        print(f"Saved checkpoint: {report.get('checkpoint_id')}")
        print(f"Parts: {report.get('parts')}")

    def cmd_load(self):
        from core.bootstrap import load_state

        report = load_state()
        print(json.dumps(report, ensure_ascii=False, indent=2, default=str))

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
        print(f"AI         : {config.ai_name}")
        print(f"Mode       : {result.get('reasoning_mode')}")
        print(f"Confidence : {result.get('confidence')}")
        print(f"Decision   : {result.get('decision', {}).get('action')}")
        print(f"LLM used   : {result.get('llm_used')}")
        print(f"Conclusion : {result.get('conclusion')}")

    def cmd_agent(self, args):
        from agents.manager import agent_manager

        agent = agent_manager.create(args.type)
        res = agent_manager.run(agent.id, args.task)
        if args.json:
            print(
                json.dumps(
                    {"success": res.success, "output": res.output, "error": res.error},
                    ensure_ascii=False,
                    indent=2,
                    default=str,
                )
            )
            return
        print(f"Success : {res.success}")
        print(f"Output  : {res.output}")

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
        print(f"Lesson     : {report.get('name')} ({report.get('lesson_id')})")
        print(f"Injected   : {report.get('injected')}")
        st = report.get("self_test") or {}
        print(f"Self-test  : {st.get('passed')}/{st.get('total')} passed")

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
        print(f"Volume     : {report.get('name')} ({report.get('volume')})")
        print(f"Lessons    : {report.get('lessons_passed')}/{report.get('lessons_total')} passed")

    def cmd_volumes(self):
        from curriculum import CurriculumEngine, load_volume

        eng = CurriculumEngine()
        for vid in eng.list_volumes():
            try:
                meta = load_volume(vid)
                print(f"{meta.get('volume')} | {meta.get('name')} v{meta.get('version')}")
            except Exception as e:
                print(f"{vid}: {e}")

    def cmd_lessons(self):
        from curriculum import CurriculumEngine

        eng = CurriculumEngine()
        print("Lessons:", eng.list_available())

    def cmd_status(self):
        from core.bootstrap import leon_status

        print(json.dumps(leon_status(), ensure_ascii=False, indent=2, default=str))

    def cmd_info(self):
        kernel.initialize()
        info = kernel.get_system_resources()
        print(f"{config.ai_name}")
        print(f"  leon_dir : {config.path.leon_dir}")
        print(f"  LLM      : {config.llm.provider} / {config.llm.model}")
        print(f"  State    : {info.get('state')}")

    def cmd_llm_check(self):
        from brain.llm.client import get_llm_client

        client = get_llm_client(force_new=True)
        print(json.dumps(client.health_check(), ensure_ascii=False, indent=2))

    def train_model(self, args):
        logger.error("train: use original pipeline; focus is cognitive path")

    def predict(self, args):
        logger.error("predict: optional ML path")

    def list_models(self):
        print("(none)")


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
        elif cmd == "train":
            ctrl.train_model(args)
        elif cmd == "predict":
            ctrl.predict(args)
        elif cmd == "list_models":
            ctrl.list_models()
        else:
            print("Leon CLI – --help")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
