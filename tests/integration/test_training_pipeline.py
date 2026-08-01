"""
Integration Tests for Training Pipeline
Tests for the complete training workflow.
"""

import os
import unittest
import tempfile
import shutil
import numpy as np
import torch

# Add the project root to the path
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from data.preprocessing.clean import DataCleaner
from data.preprocessing.normalize import DataNormalizer
from models.ml.supervised.linear_regression import LinearRegression
from models.dl.nn.simple_nn import SimpleNN
from training.trainers.supervised_trainer import SupervisedTrainer
from training.optimizers.custom_optimizers import AdamW, SGDW
from training.loss_functions.custom_losses import FocalLoss, ContrastiveLoss
from training.metrics.classification_metrics import ClassificationMetrics


class TestTrainingPipeline(unittest.TestCase):
    """Tests for the complete training pipeline."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_ml_pipeline(self):
        """Test machine learning training pipeline."""
        # Generate synthetic data
        np.random.seed(42)
        X = np.random.randn(100, 5)
        y = 2 * X[:, 0] + 3 * X[:, 1] + 1 + np.random.randn(100) * 0.1

        # Preprocess data
        cleaner = DataCleaner(verbose=False)
        X_clean = cleaner.handle_missing_values(X, strategy="fill", fill_value=0)

        normalizer = DataNormalizer(verbose=False)
        X_norm = normalizer.z_score_normalize(X_clean)

        # Train model
        model = LinearRegression()
        model.fit(X_norm, y)

        # Evaluate
        predictions = model.predict(X_norm)
        self.assertEqual(len(predictions), 100)

        # Check that model learned something
        score = model.score(X_norm, y)
        self.assertGreater(score, 0.5)  # Should have reasonable R^2

    def test_dl_pipeline(self):
        """Test deep learning training pipeline."""
        # Generate synthetic data
        torch.manual_seed(42)
        X = torch.randn(100, 10)
        y = torch.randn(100, 1)

        # Create model
        model = SimpleNN(
            input_size=10,
            hidden_sizes=[32, 16],
            output_size=1,
        )

        # Create trainer
        trainer = SupervisedTrainer(
            model=model,
            optimizer=torch.optim.Adam(model.parameters(), lr=0.001),
            criterion=torch.nn.MSELoss(),
        )

        # Train
        history = trainer.train(
            X_train=X,
            y_train=y,
            epochs=5,
            batch_size=10,
        )

        # Check training history
        self.assertIn("loss", history)
        self.assertEqual(len(history["loss"]), 5)

        # Make predictions
        predictions = trainer.predict(X)
        self.assertEqual(predictions.shape, (100, 1))

    def test_custom_optimizer_pipeline(self):
        """Test training with custom optimizer."""
        # Generate synthetic data
        torch.manual_seed(42)
        X = torch.randn(50, 5)
        y = torch.randn(50, 1)

        # Create model
        model = SimpleNN(
            input_size=5,
            hidden_sizes=[16],
            output_size=1,
        )

        # Create custom optimizer
        optimizer = AdamW(model.parameters(), lr=0.001, weight_decay=0.01)

        # Create trainer
        trainer = SupervisedTrainer(
            model=model,
            optimizer=optimizer,
            criterion=torch.nn.MSELoss(),
        )

        # Train
        history = trainer.train(
            X_train=X,
            y_train=y,
            epochs=3,
            batch_size=10,
        )

        # Check that training completed
        self.assertIn("loss", history)

    def test_custom_loss_pipeline(self):
        """Test training with custom loss function."""
        # Generate synthetic classification data
        torch.manual_seed(42)
        X = torch.randn(50, 5)
        y = torch.randint(0, 2, (50,))

        # Create model
        model = SimpleNN(
            input_size=5,
            hidden_sizes=[16],
            output_size=2,
        )

        # Create custom loss
        loss_fn = FocalLoss(gamma=2.0)

        # Create trainer
        trainer = SupervisedTrainer(
            model=model,
            optimizer=torch.optim.Adam(model.parameters(), lr=0.001),
            criterion=loss_fn,
        )

        # Train
        history = trainer.train(
            X_train=X,
            y_train=y,
            epochs=3,
            batch_size=10,
        )

        # Check that training completed
        self.assertIn("loss", history)

    def test_metrics_pipeline(self):
        """Test training with metrics tracking."""
        # Generate synthetic classification data
        torch.manual_seed(42)
        X = torch.randn(50, 5)
        y = torch.randint(0, 2, (50,))

        # Create model
        model = SimpleNN(
            input_size=5,
            hidden_sizes=[16],
            output_size=2,
        )

        # Create trainer with metrics
        trainer = SupervisedTrainer(
            model=model,
            optimizer=torch.optim.Adam(model.parameters(), lr=0.001),
            criterion=torch.nn.CrossEntropyLoss(),
            metrics=["accuracy"],
        )

        # Train
        history = trainer.train(
            X_train=X,
            y_train=y,
            epochs=3,
            batch_size=10,
        )

        # Check that metrics were tracked
        self.assertIn("accuracy", history)

    def test_data_preprocessing_pipeline(self):
        """Test complete data preprocessing pipeline."""
        # Generate synthetic data with missing values and outliers
        np.random.seed(42)
        data = np.random.randn(100, 5)
        data[0, 0] = np.nan  # Add missing value
        data[1, 1] = 100  # Add outlier

        # Clean data
        cleaner = DataCleaner(verbose=False)
        data_clean = cleaner.handle_missing_values(data, strategy="fill", fill_value=0)
        data_clean = cleaner.handle_outliers(data_clean, method="zscore", threshold=2.0)

        # Normalize data
        normalizer = DataNormalizer(verbose=False)
        data_norm = normalizer.z_score_normalize(data_clean)

        # Check that data is clean
        self.assertFalse(np.isnan(data_norm).any())
        self.assertTrue(np.all(np.abs(data_norm) < 10))  # Outliers should be capped

    def test_model_saving_pipeline(self):
        """Test model saving and loading pipeline."""
        # Generate synthetic data
        torch.manual_seed(42)
        X = torch.randn(50, 5)
        y = torch.randn(50, 1)

        # Create and train model
        model = SimpleNN(
            input_size=5,
            hidden_sizes=[16],
            output_size=1,
        )

        trainer = SupervisedTrainer(
            model=model,
            optimizer=torch.optim.Adam(model.parameters(), lr=0.001),
            criterion=torch.nn.MSELoss(),
        )

        trainer.train(
            X_train=X,
            y_train=y,
            epochs=3,
            batch_size=10,
        )

        # Save model
        model_path = os.path.join(self.temp_dir, "test_model.pt")
        trainer.save_model(model_path)

        # Check that file exists
        self.assertTrue(os.path.exists(model_path))

        # Load model
        new_model = SimpleNN(
            input_size=5,
            hidden_sizes=[16],
            output_size=1,
        )
        new_model.load_state_dict(torch.load(model_path, map_location="cpu"))

        # Make predictions with loaded model
        new_trainer = SupervisedTrainer(
            model=new_model,
            optimizer=torch.optim.Adam(new_model.parameters(), lr=0.001),
            criterion=torch.nn.MSELoss(),
        )

        predictions = new_trainer.predict(X)
        self.assertEqual(predictions.shape, (50, 1))


if __name__ == "__main__":
    unittest.main()
