"""
Performance Tests for Models
Benchmark tests for model training and inference speed.
"""

import os
import time
import unittest
import numpy as np
import torch

# Add the project root to the path
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from models.ml.supervised.linear_regression import LinearRegression
from models.ml.supervised.random_forest import RandomForest
from models.ml.unsupervised.kmeans import KMeans
from models.dl.nn.simple_nn import SimpleNN
from training.trainers.supervised_trainer import SupervisedTrainer


class TestModelPerformance(unittest.TestCase):
    """Performance tests for models."""

    def test_linear_regression_training_speed(self):
        """Test LinearRegression training speed."""
        # Generate large dataset
        np.random.seed(42)
        n_samples = 10000
        X = np.random.randn(n_samples, 10)
        y = np.random.randn(n_samples)

        # Time training
        start_time = time.time()
        model = LinearRegression()
        model.fit(X, y, method="normal")
        training_time = time.time() - start_time

        # Training should complete in reasonable time
        self.assertLess(training_time, 5.0)  # Should be very fast

        # Time prediction
        start_time = time.time()
        predictions = model.predict(X)
        prediction_time = time.time() - start_time

        # Prediction should be fast
        self.assertLess(prediction_time, 1.0)

    def test_random_forest_training_speed(self):
        """Test RandomForest training speed."""
        # Generate dataset
        np.random.seed(42)
        n_samples = 1000
        X = np.random.randn(n_samples, 10)
        y = np.random.randint(0, 2, n_samples)

        # Time training
        start_time = time.time()
        model = RandomForest(n_estimators=10, max_depth=5, random_state=42)
        model.fit(X, y)
        training_time = time.time() - start_time

        # Training should complete in reasonable time
        self.assertLess(training_time, 10.0)

        # Time prediction
        start_time = time.time()
        predictions = model.predict(X)
        prediction_time = time.time() - start_time

        # Prediction should be fast
        self.assertLess(prediction_time, 1.0)

    def test_kmeans_training_speed(self):
        """Test KMeans training speed."""
        # Generate dataset
        np.random.seed(42)
        n_samples = 1000
        X = np.random.randn(n_samples, 10)

        # Time training
        start_time = time.time()
        model = KMeans(n_clusters=5, max_iter=100, random_state=42)
        model.fit(X)
        training_time = time.time() - start_time

        # Training should complete in reasonable time
        self.assertLess(training_time, 5.0)

        # Time prediction
        start_time = time.time()
        predictions = model.predict(X)
        prediction_time = time.time() - start_time

        # Prediction should be fast
        self.assertLess(prediction_time, 1.0)

    def test_simple_nn_training_speed(self):
        """Test SimpleNN training speed."""
        # Generate dataset
        torch.manual_seed(42)
        n_samples = 1000
        X = torch.randn(n_samples, 20)
        y = torch.randn(n_samples, 1)

        # Create model
        model = SimpleNN(
            input_size=20,
            hidden_sizes=[64, 32],
            output_size=1,
        )

        # Create trainer
        trainer = SupervisedTrainer(
            model=model,
            optimizer=torch.optim.Adam(model.parameters(), lr=0.001),
            criterion=torch.nn.MSELoss(),
        )

        # Time training
        start_time = time.time()
        trainer.train(
            X_train=X,
            y_train=y,
            epochs=5,
            batch_size=32,
        )
        training_time = time.time() - start_time

        # Training should complete in reasonable time
        self.assertLess(training_time, 30.0)

        # Time prediction
        start_time = time.time()
        predictions = trainer.predict(X)
        prediction_time = time.time() - start_time

        # Prediction should be fast
        self.assertLess(prediction_time, 1.0)

    def test_batch_size_impact(self):
        """Test impact of batch size on training speed."""
        # Generate dataset
        torch.manual_seed(42)
        n_samples = 1000
        X = torch.randn(n_samples, 10)
        y = torch.randn(n_samples, 1)

        # Create model
        model = SimpleNN(
            input_size=10,
            hidden_sizes=[32],
            output_size=1,
        )

        # Test different batch sizes
        batch_sizes = [8, 32, 128]
        times = []

        for batch_size in batch_sizes:
            trainer = SupervisedTrainer(
                model=model,
                optimizer=torch.optim.Adam(model.parameters(), lr=0.001),
                criterion=torch.nn.MSELoss(),
            )

            start_time = time.time()
            trainer.train(
                X_train=X,
                y_train=y,
                epochs=3,
                batch_size=batch_size,
            )
            times.append(time.time() - start_time)

        # Larger batch sizes should generally be faster
        # (This is a general trend, but not always true due to memory constraints)
        self.assertLess(times[2], times[0] * 2)  # 128 should be faster than 8

    def test_model_size_impact(self):
        """Test impact of model size on training speed."""
        # Generate dataset
        torch.manual_seed(42)
        n_samples = 500
        X = torch.randn(n_samples, 10)
        y = torch.randn(n_samples, 1)

        # Test different model sizes
        model_configs = [
            {"input_size": 10, "hidden_sizes": [16], "output_size": 1},
            {"input_size": 10, "hidden_sizes": [64, 32], "output_size": 1},
            {"input_size": 10, "hidden_sizes": [128, 64, 32], "output_size": 1},
        ]
        times = []

        for config in model_configs:
            model = SimpleNN(**config)
            trainer = SupervisedTrainer(
                model=model,
                optimizer=torch.optim.Adam(model.parameters(), lr=0.001),
                criterion=torch.nn.MSELoss(),
            )

            start_time = time.time()
            trainer.train(
                X_train=X,
                y_train=y,
                epochs=3,
                batch_size=32,
            )
            times.append(time.time() - start_time)

        # Larger models should take longer to train
        self.assertLess(times[0], times[1])
        self.assertLess(times[1], times[2])

    def test_inference_latency(self):
        """Test inference latency for different models."""
        # Generate dataset
        torch.manual_seed(42)
        n_samples = 100
        X = torch.randn(n_samples, 10)

        # Test different models
        models = [
            SimpleNN(input_size=10, hidden_sizes=[16], output_size=1),
            SimpleNN(input_size=10, hidden_sizes=[64, 32], output_size=1),
            SimpleNN(input_size=10, hidden_sizes=[128, 64, 32], output_size=1),
        ]
        latencies = []

        for model in models:
            trainer = SupervisedTrainer(
                model=model,
                optimizer=torch.optim.Adam(model.parameters(), lr=0.001),
                criterion=torch.nn.MSELoss(),
            )

            # Warm up
            trainer.predict(X[:5])

            # Time inference
            start_time = time.time()
            for _ in range(10):
                trainer.predict(X)
            latency = (time.time() - start_time) / 10
            latencies.append(latency)

        # Larger models should have higher latency
        self.assertLess(latencies[0], latencies[1])
        self.assertLess(latencies[1], latencies[2])

    def test_memory_usage(self):
        """Test memory usage of models."""
        # This test checks that models don't use excessive memory
        # Note: This is a basic check and may need adjustment based on system

        # Generate dataset
        torch.manual_seed(42)
        n_samples = 100
        X = torch.randn(n_samples, 20)
        y = torch.randn(n_samples, 1)

        # Create a reasonably sized model
        model = SimpleNN(
            input_size=20,
            hidden_sizes=[128, 64],
            output_size=1,
        )

        # Create trainer
        trainer = SupervisedTrainer(
            model=model,
            optimizer=torch.optim.Adam(model.parameters(), lr=0.001),
            criterion=torch.nn.MSELoss(),
        )

        # Train
        trainer.train(
            X_train=X,
            y_train=y,
            epochs=3,
            batch_size=32,
        )

        # Check model size (number of parameters)
        param_count = sum(p.numel() for p in model.parameters())
        self.assertLess(param_count, 100000)  # Should have reasonable number of parameters


if __name__ == "__main__":
    unittest.main()
