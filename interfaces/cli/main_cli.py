"""
Main CLI – ML training + ThinkingBrain / Orchestrator əmrləri.
"""

import argparse
import sys
import json
from typing import Optional, Dict, Any

from core.logger import logger
from core.config import config
from core.kernel import kernel


def parse_args():
    parser = argparse.ArgumentParser(
        description="Zenthon AI Platform CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m interfaces.cli.main_cli think "Süni intellekt nədir?"
  python -m interfaces.cli.main_cli think "Plan yaz" --mode sot --goal "MVP"
  python -m interfaces.cli.main_cli agent coding "Fibonacci funksiyası yaz"
  python -m interfaces.cli.main_cli status
  python -m interfaces.cli.main_cli train --model linear_regression --data train.csv --target y
        """,
    )
    sub = parser.add_subparsers(dest="command")

    # ── think ──
    think_p = sub.add_parser("think", help="ThinkingBrain ilə düşün")
    think_p.add_argument("query", type=str, help="Sual / tapşırıq")
    think_p.add_argument("--mode", default="auto", choices=["auto", "cot", "tot", "sot"])
    think_p.add_argument("--goal", default=None)
    think_p.add_argument("--agent", default=None, help="Əlavə agent: coding|research|executor|vision|voice")
    think_p.add_argument("--json", action="store_true", help="JSON çıxış")

    # ── agent ──
    agent_p = sub.add_parser("agent", help="Agent işə sal")
    agent_p.add_argument("type", choices=["coding", "research", "executor", "vision", "voice"])
    agent_p.add_argument("task", type=str)
    agent_p.add_argument("--json", action="store_true")

    # ── status ──
    sub.add_parser("status", help="Platform status")

    # ── info ──
    sub.add_parser("info", help="Sistem məlumatı")

    # ── train (mövcud) ──
    train_p = sub.add_parser("train", help="Model öyrət")
    train_p.add_argument("--model", required=True, choices=["linear_regression", "random_forest", "kmeans", "simple_nn"])
    train_p.add_argument("--data", required=True)
    train_p.add_argument("--target", required=True)
    train_p.add_argument("--test_size", type=float, default=0.2)
    train_p.add_argument("--epochs", type=int, default=10)
    train_p.add_argument("--batch_size", type=int, default=32)
    train_p.add_argument("--learning_rate", type=float, default=0.001)
    train_p.add_argument("--save_model", default=None)

    # ── predict ──
    pred_p = sub.add_parser("predict", help="Proqnoz")
    pred_p.add_argument("--model", required=True)
    pred_p.add_argument("--data", required=True)
    pred_p.add_argument("--output", default=None)

    # ── list_models ──
    sub.add_parser("list_models", help="Yüklənmiş modellər")

    return parser.parse_args()


class CLIController:
    def __init__(self):
        self.models = {}
        self.predictors = {}

    def cmd_think(self, args):
        from brain.orchestrator import BrainOrchestrator

        orch = BrainOrchestrator()
        result = orch.run(
            args.query,
            goal=args.goal,
            reasoning_mode=args.mode,
            agent_type=args.agent,
        )
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
            return
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
            print(json.dumps({"success": res.success, "output": res.output, "error": res.error, "metadata": res.metadata}, ensure_ascii=False, indent=2, default=str))
            return
        print(f"Success : {res.success}")
        if res.error:
            print(f"Error   : {res.error}")
        print(f"Output  : {res.output}")

    def cmd_status(self):
        from brain.orchestrator import BrainOrchestrator

        kernel.initialize()
        orch = BrainOrchestrator()
        st = orch.status()
        print(json.dumps(st, ensure_ascii=False, indent=2, default=str))

    def cmd_info(self):
        kernel.initialize()
        info = kernel.get_system_resources()
        print("Zenthon System Info")
        print(f"  State : {info.get('state')}")
        print(f"  CPU   : {info.get('cpu_percent')}%")
        mem = info.get("memory") or {}
        print(f"  RAM   : {mem.get('percent')}%")
        print(f"  Services: {kernel.status().get('services')}")

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
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=args.test_size, random_state=42)
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
        if args.command == "think":
            ctrl.cmd_think(args)
        elif args.command == "agent":
            ctrl.cmd_agent(args)
        elif args.command == "status":
            ctrl.cmd_status()
        elif args.command == "info":
            ctrl.cmd_info()
        elif args.command == "train":
            ctrl.train_model(args)
        elif args.command == "predict":
            ctrl.predict(args)
        elif args.command == "list_models":
            ctrl.list_models()
        else:
            print("Əmr yoxdur. --help bax.")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
