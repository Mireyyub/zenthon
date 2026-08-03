"""
Leon CLI – start / smoke / think / curriculum / ML.
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
  python -m interfaces.cli.main_cli status
  python -m interfaces.cli.main_cli think "Obyekt nədir?"
  python -m interfaces.cli.main_cli teach-volume 01
        """,
    )
    sub = parser.add_subparsers(dest="command")

    start_p = sub.add_parser("start", help="Leon bootstrap (kernel + paths + llm check)")
    start_p.add_argument("--bootstrap", action="store_true", help="Curriculum + genome")
    start_p.add_argument("--volume", default="01")
    start_p.add_argument("--no-llm-check", action="store_true")
    start_p.add_argument("--json", action="store_true")

    sub.add_parser("smoke", help="Faza 0 smoke test")

    think_p = sub.add_parser("think", help="Leon ThinkingBrain ilə düşün")
    think_p.add_argument("query", type=str)
    think_p.add_argument("--mode", default="auto", choices=["auto", "cot", "tot", "sot"])
    think_p.add_argument("--goal", default=None)
    think_p.add_argument("--agent", default=None)
    think_p.add_argument("--json", action="store_true")

    agent_p = sub.add_parser("agent", help="Agent işə sal")
    agent_p.add_argument(
        "type",
        choices=["coding", "research", "executor", "vision", "voice", "react", "pev", "reflexion"],
    )
    agent_p.add_argument("task", type=str)
    agent_p.add_argument("--json", action="store_true")

    teach_p = sub.add_parser("teach", help="Tək curriculum dərsini öyrət")
    teach_p.add_argument("lesson_id", nargs="?", default="000001")
    teach_p.add_argument("--volume", default=None)
    teach_p.add_argument("--json", action="store_true")

    tv = sub.add_parser("teach-volume", help="Bütün cild dərslərini öyrət")
    tv.add_argument("volume_id", nargs="?", default="01")
    tv.add_argument("--json", action="store_true")

    sub.add_parser("volumes", help="Genesis cildləri")
    sub.add_parser("lessons", help="Dərslər")
    sub.add_parser("status", help="Platform status (əskiklər daxil)")
    sub.add_parser("info", help="Sistem məlumatı")
    sub.add_parser("llm-check", help="LLM / Ollama yoxlaması")

    train_p = sub.add_parser("train", help="Model öyrət")
    train_p.add_argument("--model", required=True, choices=["linear_regression", "random_forest", "kmeans", "simple_nn"])
    train_p.add_argument("--data", required=True)
    train_p.add_argument("--target", required=True)
    train_p.add_argument("--test_size", type=float, default=0.2)
    train_p.add_argument("--epochs", type=int, default=10)
    train_p.add_argument("--batch_size", type=int, default=32)
    train_p.add_argument("--learning_rate", type=float, default=0.001)
    train_p.add_argument("--save_model", default=None)

    pred_p = sub.add_parser("predict", help="Proqnoz")
    pred_p.add_argument("--model", required=True)
    pred_p.add_argument("--data", required=True)
    pred_p.add_argument("--output", default=None)

    sub.add_parser("list_models", help="Yüklənmiş modellər")

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
        )
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
            return
        print(f"AI: {config.ai_name}")
        print(f"leon_dir: {config.path.leon_dir}")
        for step in report.get("steps") or []:
            mark = "OK" if step.get("ok") else "FAIL"
            extra = step.get("error") or step.get("model") or ""
            print(f"  [{mark}] {step.get('step')} {extra}")
        for w in report.get("warnings") or []:
            print(f"  WARN: {w}")
        for k, v in (report.get("services") or {}).items():
            print(f"  service {k}: {v}")

    def cmd_smoke(self):
        from core.bootstrap import smoke_test

        report = smoke_test()
        print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
        print("SMOKE:", "PASS" if report.get("overall_ok") else "FAIL")
        if not report.get("overall_ok"):
            sys.exit(1)

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
        if result.get("reflection"):
            print(f"Reflection : {result['reflection']}")
        print(f"Conclusion : {result.get('conclusion')}")
        if result.get("agent"):
            print(f"Agent      : {result['agent']}")

    def cmd_agent(self, args):
        from agents.manager import agent_manager

        agent = agent_manager.create(args.type)
        res = agent_manager.run(agent.id, args.task)
        if args.json:
            print(
                json.dumps(
                    {
                        "success": res.success,
                        "output": res.output,
                        "error": res.error,
                        "metadata": res.metadata,
                    },
                    ensure_ascii=False,
                    indent=2,
                    default=str,
                )
            )
            return
        print(f"Success : {res.success}")
        if res.error:
            print(f"Error   : {res.error}")
        print(f"Output  : {res.output}")

    def cmd_teach(self, args):
        from curriculum import CurriculumEngine

        eng = CurriculumEngine()
        report = eng.teach(args.lesson_id, volume_id=getattr(args, "volume", None))
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
            return
        print(f"Lesson     : {report.get('name')} ({report.get('lesson_id')})")
        print(f"Volume     : {report.get('volume')}")
        print(f"Goal       : {report.get('goal')}")
        print(f"Injected   : {report.get('injected')}")
        st = report.get("self_test") or {}
        print(f"Self-test  : {st.get('passed')}/{st.get('total')} passed")
        for case in st.get("cases") or []:
            mark = "OK" if case.get("pass") else "FAIL"
            print(f"  [{mark}] {case.get('input')} → {case.get('predicted')} (expected {case.get('expected')})")

    def cmd_teach_volume(self, args):
        from curriculum import CurriculumEngine

        eng = CurriculumEngine()
        report = eng.teach_volume(args.volume_id)
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
            return
        print(f"Volume     : {report.get('name')} ({report.get('volume')})")
        print(f"Version    : {report.get('version')}")
        print(f"Targets    : {', '.join(report.get('target_concepts') or [])}")
        print(f"Lessons    : {report.get('lessons_passed')}/{report.get('lessons_total')} passed")
        for r in report.get("reports") or []:
            st = r.get("self_test") or {}
            print(f"  - {r.get('lesson_id')} {r.get('name')}: {st.get('passed')}/{st.get('total')}")

    def cmd_volumes(self):
        from curriculum import CurriculumEngine, load_volume

        eng = CurriculumEngine()
        for vid in eng.list_volumes():
            try:
                meta = load_volume(vid)
                print(f"{meta.get('volume')} | {meta.get('name')} v{meta.get('version')}")
                print(f"  lessons: {meta.get('lessons')}")
                print(f"  targets: {meta.get('target_concepts')}")
            except Exception as e:
                print(f"{vid}: error {e}")

    def cmd_lessons(self):
        from curriculum import CurriculumEngine

        eng = CurriculumEngine()
        print("Volumes:", eng.list_volumes())
        print("Lessons:", eng.list_available() or "(none)")
        st = eng.status()
        print("Taught lessons:", st.get("taught_lessons"))
        print("Taught volumes:", st.get("taught_volumes"))

    def cmd_status(self):
        from core.bootstrap import leon_status

        print(json.dumps(leon_status(), ensure_ascii=False, indent=2, default=str))

    def cmd_info(self):
        kernel.initialize()
        info = kernel.get_system_resources()
        print(f"{config.ai_name} System Info")
        print(f"  State    : {info.get('state')}")
        print(f"  CPU      : {info.get('cpu_percent')}%")
        mem = info.get("memory") or {}
        print(f"  RAM      : {mem.get('percent')}%")
        print(f"  leon_dir : {config.path.leon_dir}")
        print(f"  LLM      : {config.llm.provider} / {config.llm.model}")
        print(f"  Services : {kernel.status().get('services')}")

    def cmd_llm_check(self):
        from brain.llm.client import get_llm_client

        client = get_llm_client(force_new=True)
        report = client.health_check()
        print(json.dumps(report, ensure_ascii=False, indent=2))
        emb = client.embed("Leon AI platform test")
        print(f"embedding_dims: {len(emb) if emb else None}")

    def train_model(self, args):
        import pandas as pd
        from sklearn.model_selection import train_test_split
        from sklearn.preprocessing import StandardScaler
        from models.ml.supervised.linear_regression import LinearRegression
        from models.ml.supervised.random_forest import RandomForest
        from models.ml.unsupervised.kmeans import KMeans
        from inference.predictors.model_predictor import ModelPredictor

        logger.info(f"Training {args.model}...")
        data = pd.read_csv(args.data)
        X = data.drop(columns=[args.target]).values
        y = data[args.target].values
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=args.test_size, random_state=42
        )
        scaler = StandardScaler()
        X_train = scaler.fit_transform(X_train)
        X_test = scaler.transform(X_test)

        if args.model == "linear_regression":
            model = LinearRegression()
            model.fit(X_train, y_train)
            score = model.score(X_test, y_test)
        elif args.model == "random_forest":
            model = RandomForest(n_estimators=100, random_state=42)
            model.fit(X_train, y_train)
            score = model.score(X_test, y_test)
        elif args.model == "kmeans":
            model = KMeans(n_clusters=3, random_state=42)
            model.fit(X)
            score = None
        else:
            logger.error("simple_nn üçün torch pipeline ayrıca işə salınmalıdır")
            return

        logger.info(f"Trained. Score={score}")
        self.models[args.model] = model
        self.predictors[args.model] = ModelPredictor(model=model, model_type="sklearn")
        if args.save_model:
            import joblib

            joblib.dump(model, args.save_model)
            logger.info(f"Saved → {args.save_model}")

    def predict(self, args):
        import pandas as pd

        if args.model not in self.predictors:
            logger.error(f"Model yoxdur: {args.model}")
            return
        data = pd.read_csv(args.data)
        preds = self.predictors[args.model].predict(data.values)
        if args.output:
            pd.DataFrame({"prediction": preds}).to_csv(args.output, index=False)
        else:
            print(preds)

    def list_models(self):
        print("Loaded:", list(self.models.keys()) or "(none)")


def main():
    args = parse_args()
    ctrl = CLIController()
    try:
        if args.command == "start":
            ctrl.cmd_start(args)
        elif args.command == "smoke":
            ctrl.cmd_smoke()
        elif args.command == "think":
            ctrl.cmd_think(args)
        elif args.command == "agent":
            ctrl.cmd_agent(args)
        elif args.command == "teach":
            ctrl.cmd_teach(args)
        elif args.command == "teach-volume":
            ctrl.cmd_teach_volume(args)
        elif args.command == "volumes":
            ctrl.cmd_volumes()
        elif args.command == "lessons":
            ctrl.cmd_lessons()
        elif args.command == "status":
            ctrl.cmd_status()
        elif args.command == "info":
            ctrl.cmd_info()
        elif args.command == "llm-check":
            ctrl.cmd_llm_check()
        elif args.command == "train":
            ctrl.train_model(args)
        elif args.command == "predict":
            ctrl.predict(args)
        elif args.command == "list_models":
            ctrl.list_models()
        else:
            print("Leon CLI – əmr yoxdur. --help bax.")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
