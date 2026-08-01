"""
Main CLI Module
Command-line interface for AI System.
"""

import argparse
import sys
import json
import time
from typing import Optional, Dict, Any, List

from core.logger import logger
from core.config import config
from core.kernel import kernel
from data.storage.database import SQLiteDatabase
from models.ml.supervised.linear_regression import LinearRegression
from models.ml.supervised.random_forest import RandomForest
from models.ml.unsupervised.kmeans import KMeans
from models.dl.nn.simple_nn import SimpleNN
from training.trainers.supervised_trainer import SupervisedTrainer
from inference.predictors.model_predictor import ModelPredictor


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="AI System - Command Line Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Train a linear regression model
  python -m interfaces.cli.main_cli train --model linear_regression --data train.csv --target y

  # Make predictions with a trained model
  python -m interfaces.cli.main_cli predict --model linear_regression --data test.csv

  # Evaluate a model
  python -m interfaces.cli.main_cli evaluate --model linear_regression --data test.csv
        """,
    )

    # Main commands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Train command
    train_parser = subparsers.add_parser("train", help="Train a model")
    train_parser.add_argument(
        "--model",
        type=str,
        required=True,
        choices=["linear_regression", "random_forest", "kmeans", "simple_nn"],
        help="Model to train",
    )
    train_parser.add_argument(
        "--data",
        type=str,
        required=True,
        help="Path to training data (CSV file)",
    )
    train_parser.add_argument(
        "--target",
        type=str,
        required=True,
        help="Target column name",
    )
    train_parser.add_argument(
        "--test_size",
        type=float,
        default=0.2,
        help="Fraction of data to use for testing",
    )
    train_parser.add_argument(
        "--epochs",
        type=int,
        default=10,
        help="Number of training epochs (for neural networks)",
    )
    train_parser.add_argument(
        "--batch_size",
        type=int,
        default=32,
        help="Batch size for training",
    )
    train_parser.add_argument(
        "--learning_rate",
        type=float,
        default=0.001,
        help="Learning rate for training",
    )
    train_parser.add_argument(
        "--save_model",
        type=str,
        default=None,
        help="Path to save the trained model",
    )

    # Predict command
    predict_parser = subparsers.add_parser("predict", help="Make predictions")
    predict_parser.add_argument(
        "--model",
        type=str,
        required=True,
        help="Model to use for predictions",
    )
    predict_parser.add_argument(
        "--data",
        type=str,
        required=True,
        help="Path to input data (CSV file)",
    )
    predict_parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to save predictions",
    )

    # Evaluate command
    eval_parser = subparsers.add_parser("evaluate", help="Evaluate a model")
    eval_parser.add_argument(
        "--model",
        type=str,
        required=True,
        help="Model to evaluate",
    )
    eval_parser.add_argument(
        "--data",
        type=str,
        required=True,
        help="Path to evaluation data (CSV file)",
    )
    eval_parser.add_argument(
        "--target",
        type=str,
        required=True,
        help="Target column name",
    )

    # Info command
    subparsers.add_parser("info", help="Show system information")

    # List models command
    subparsers.add_parser("list_models", help="List available models")

    return parser.parse_args()


class CLIController:
    """Controller for CLI operations."""

    def __init__(self):
        self.models = {}
        self.trainers = {}
        self.predictors = {}
        self.db = SQLiteDatabase()

    def train_model(self, args: argparse.Namespace) -> None:
        """Train a model based on CLI arguments."""
        import pandas as pd
        from sklearn.model_selection import train_test_split
        from sklearn.preprocessing import StandardScaler

        logger.info(f"Training {args.model} model...")

        # Load data
        data = pd.read_csv(args.data)
        X = data.drop(columns=[args.target])
        y = data[args.target]

        # Preprocess data
        if args.model in ["linear_regression", "random_forest"]:
            # For scikit-learn models, convert to numpy
            X = X.values
            y = y.values

            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=args.test_size, random_state=42
            )

            # Standardize data
            scaler = StandardScaler()
            X_train = scaler.fit_transform(X_train)
            X_test = scaler.transform(X_test)

            # Train model
            if args.model == "linear_regression":
                model = LinearRegression()
                model.fit(X_train, y_train)
            elif args.model == "random_forest":
                model = RandomForest(n_estimators=100, random_state=42)
                model.fit(X_train, y_train)

            # Evaluate
            score = model.score(X_test, y_test)
            logger.info(f"Model trained. Test score: {score:.4f}")

            # Save model if requested
            if args.save_model:
                import joblib
                joblib.dump(model, args.save_model)
                logger.info(f"Model saved to {args.save_model}")

            # Store model
            self.models[args.model] = model
            self.predictors[args.model] = ModelPredictor(
                model=model,
                model_type="sklearn",
            )

        elif args.model == "kmeans":
            # For unsupervised learning
            X = X.values
            model = KMeans(n_clusters=3, random_state=42)
            model.fit(X)
            logger.info("KMeans model trained")
            self.models[args.model] = model

        elif args.model == "simple_nn":
            # For neural networks
            import torch
            from torch.utils.data import DataLoader, TensorDataset

            X = X.values
            y = y.values

            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=args.test_size, random_state=42
            )

            # Standardize data
            scaler = StandardScaler()
            X_train = scaler.fit_transform(X_train)
            X_test = scaler.transform(X_test)

            # Convert to tensors
            X_train = torch.from_numpy(X_train).float()
            y_train = torch.from_numpy(y_train).float()
            X_test = torch.from_numpy(X_test).float()
            y_test = torch.from_numpy(y_test).float()

            # Create model
            input_size = X_train.shape[1]
            model = SimpleNN(
                input_size=input_size,
                hidden_sizes=[64, 32],
                output_size=1,
            )

            # Create trainer
            trainer = SupervisedTrainer(
                model=model,
                optimizer=None,
                criterion=None,
            )

            # Train
            trainer.train(
                X_train=X_train,
                y_train=y_train,
                X_val=X_test,
                y_val=y_test,
                epochs=args.epochs,
                batch_size=args.batch_size,
            )

            # Save model if requested
            if args.save_model:
                torch.save(model.state_dict(), args.save_model)
                logger.info(f"Model saved to {args.save_model}")

            # Store model
            self.models[args.model] = model
            self.predictors[args.model] = ModelPredictor(
                model=model,
                model_type="pytorch",
            )

        logger.info(f"Training completed for {args.model}")

    def predict(self, args: argparse.Namespace) -> None:
        """Make predictions using a trained model."""
        import pandas as pd

        logger.info(f"Making predictions with {args.model} model...")

        if args.model not in self.predictors:
            logger.error(f"Model {args.model} not found. Available models: {list(self.predictors.keys())}")
            return

        # Load data
        data = pd.read_csv(args.data)
        X = data.values

        # Make predictions
        predictor = self.predictors[args.model]
        predictions = predictor.predict(X)

        # Save predictions if requested
        if args.output:
            pd.DataFrame({"prediction": predictions}).to_csv(args.output, index=False)
            logger.info(f"Predictions saved to {args.output}")
        else:
            print("Predictions:")
            print(predictions)

    def evaluate_model(self, args: argparse.Namespace) -> None:
        """Evaluate a trained model."""
        import pandas as pd
        from sklearn.metrics import mean_squared_error, accuracy_score

        logger.info(f"Evaluating {args.model} model...")

        if args.model not in self.predictors:
            logger.error(f"Model {args.model} not found. Available models: {list(self.predictors.keys())}")
            return

        # Load data
        data = pd.read_csv(args.data)
        X = data.drop(columns=[args.target])
        y = data[args.target]

        # Make predictions
        predictor = self.predictors[args.model]
        predictions = predictor.predict(X.values)

        # Calculate metrics
        if hasattr(predictions, "shape") and len(predictions.shape) > 1:
            # Classification
            predictions = predictions.argmax(axis=1)
            accuracy = accuracy_score(y.values, predictions)
            logger.info(f"Accuracy: {accuracy:.4f}")
        else:
            # Regression
            mse = mean_squared_error(y.values, predictions)
            logger.info(f"Mean Squared Error: {mse:.4f}")

    def show_info(self) -> None:
        """Show system information."""
        logger.info("=" * 60)
        logger.info("AI System - System Information")
        logger.info("=" * 60)

        # System info
        system_info = kernel.get_system_resources()
        logger.info("\nSystem Resources:")
        logger.info(f"  CPU Usage: {system_info['cpu_percent']:.2f}%")
        logger.info(f"  Memory Usage: {system_info['memory']['percent']:.2f}%")

        # GPU info
        if system_info['gpu']:
            logger.info("\nGPU Information:")
            for gpu_name, gpu_data in system_info['gpu'].items():
                logger.info(f"  {gpu_name}:")
                logger.info(f"    Memory Used: {gpu_data['memory_used']}MB")
                logger.info(f"    Memory Total: {gpu_data['memory_total']}MB")
                logger.info(f"    Utilization: {gpu_data['utilization']:.2f}%")

        # Configuration
        logger.info("\nConfiguration:")
        logger.info(f"  Base Directory: {config.path.base_dir}")
        logger.info(f"  Models Directory: {config.path.models_dir}")
        logger.info(f"  Data Directory: {config.path.data_dir}")

        # Loaded models
        logger.info(f"\nLoaded Models: {len(self.models)}")
        for model_name in self.models:
            logger.info(f"  - {model_name}")

        logger.info("=" * 60)

    def list_models(self) -> None:
        """List available models."""
        logger.info("Available Models:")
        logger.info("-" * 40)

        if not self.models:
            logger.info("No models loaded")
        else:
            for model_name, model in self.models.items():
                logger.info(f"  {model_name}: {type(model).__name__}")


def main():
    """Main entry point for CLI."""
    args = parse_args()
    controller = CLIController()

    try:
        if args.command == "train":
            controller.train_model(args)
        elif args.command == "predict":
            controller.predict(args)
        elif args.command == "evaluate":
            controller.evaluate_model(args)
        elif args.command == "info":
            controller.show_info()
        elif args.command == "list_models":
            controller.list_models()
        else:
            print("Invalid command. Use --help for available commands.")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
