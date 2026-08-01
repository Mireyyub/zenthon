"""
Unit Tests for Models Module
Tests for machine learning and deep learning models.
"""

import os
import unittest
import numpy as np
import torch

# Add the project root to the path
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from models.ml.supervised.linear_regression import LinearRegression
from models.ml.supervised.random_forest import RandomForest
from models.ml.unsupervised.kmeans import KMeans
from models.dl.nn.simple_nn import SimpleNN, MLP


class TestLinearRegression(unittest.TestCase):
    """Tests for LinearRegression."""

    def test_fit_normal_equation(self):
        """Test fitting with normal equation."""
        # Create simple linear data: y = 2x + 1
        X = np.array([[1], [2], [3], [4], [5]])
        y = np.array([3, 5, 7, 9, 11])  # y = 2x + 1

        model = LinearRegression()
        model.fit(X, y, method="normal")

        # Check coefficients
        bias, weights = model.get_coefficients()
        self.assertAlmostEqual(bias, 1.0, places=5)
        self.assertAlmostEqual(weights[0], 2.0, places=5)

    def test_fit_gradient_descent(self):
        """Test fitting with gradient descent."""
        # Create simple linear data: y = 2x + 1
        X = np.array([[1], [2], [3], [4], [5]])
        y = np.array([3, 5, 7, 9, 11])  # y = 2x + 1

        model = LinearRegression()
        model.fit(X, y, method="gradient", max_iter=1000, learning_rate=0.01)

        # Check predictions
        predictions = model.predict(X)
        self.assertTrue(np.allclose(predictions, y, atol=0.1))

    def test_predict(self):
        """Test prediction."""
        X = np.array([[1], [2], [3]])
        y = np.array([3, 5, 7])

        model = LinearRegression()
        model.fit(X, y, method="normal")

        predictions = model.predict(X)
        self.assertTrue(np.allclose(predictions, y))

    def test_score(self):
        """Test R-squared score."""
        X = np.array([[1], [2], [3], [4], [5]])
        y = np.array([3, 5, 7, 9, 11])

        model = LinearRegression()
        model.fit(X, y, method="normal")

        score = model.score(X, y)
        self.assertAlmostEqual(score, 1.0, places=5)  # Perfect fit

    def test_no_intercept(self):
        """Test model without intercept."""
        X = np.array([[1], [2], [3]])
        y = np.array([2, 4, 6])  # y = 2x (no intercept)

        model = LinearRegression(fit_intercept=False)
        model.fit(X, y, method="normal")

        bias, weights = model.get_coefficients()
        self.assertIsNone(bias)
        self.assertAlmostEqual(weights[0], 2.0, places=5)


class TestRandomForest(unittest.TestCase):
    """Tests for RandomForest."""

    def test_fit_and_predict(self):
        """Test fitting and prediction."""
        # Create simple classification data
        X = np.array([
            [1, 1], [1, 2], [2, 1], [2, 2],
            [3, 3], [3, 4], [4, 3], [4, 4],
        ])
        y = np.array([0, 0, 0, 0, 1, 1, 1, 1])

        model = RandomForest(n_estimators=10, max_depth=2, random_state=42)
        model.fit(X, y)

        predictions = model.predict(X)
        # Should predict correctly for most samples
        self.assertGreater(model.score(X, y), 0.5)

    def test_predict_proba(self):
        """Test probability predictions."""
        X = np.array([[1, 1], [1, 2], [2, 1], [2, 2]])
        y = np.array([0, 0, 1, 1])

        model = RandomForest(n_estimators=10, max_depth=2, random_state=42)
        model.fit(X, y)

        probas = model.predict_proba(X)
        self.assertEqual(probas.shape, (4, 2))  # 4 samples, 2 classes
        self.assertTrue(np.all(probas >= 0))
        self.assertTrue(np.all(probas <= 1))

    def test_score(self):
        """Test accuracy score."""
        X = np.array([[1, 1], [1, 2], [2, 1], [2, 2]])
        y = np.array([0, 0, 1, 1])

        model = RandomForest(n_estimators=10, max_depth=2, random_state=42)
        model.fit(X, y)

        score = model.score(X, y)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)


class TestKMeans(unittest.TestCase):
    """Tests for KMeans."""

    def test_fit_and_predict(self):
        """Test fitting and prediction."""
        # Create simple clustering data
        X = np.array([
            [1, 1], [1, 2], [2, 1], [2, 2],
            [10, 10], [10, 11], [11, 10], [11, 11],
        ])

        model = KMeans(n_clusters=2, max_iter=100, random_state=42)
        model.fit(X)

        predictions = model.predict(X)
        # Should assign each point to a cluster
        self.assertEqual(len(predictions), 8)
        self.assertTrue(np.all(predictions >= 0))
        self.assertTrue(np.all(predictions < 2))

    def test_centroids(self):
        """Test centroid calculation."""
        X = np.array([[1, 1], [1, 2], [10, 10], [10, 11]])

        model = KMeans(n_clusters=2, max_iter=100, random_state=42)
        model.fit(X)

        centroids = model.get_centroids()
        self.assertEqual(centroids.shape, (2, 2))  # 2 clusters, 2 features

    def test_inertia(self):
        """Test inertia calculation."""
        X = np.array([[1, 1], [1, 2], [10, 10], [10, 11]])

        model = KMeans(n_clusters=2, max_iter=100, random_state=42)
        model.fit(X)

        inertia = model.get_inertia()
        self.assertGreater(inertia, 0)

    def test_fit_predict(self):
        """Test fit_predict method."""
        X = np.array([[1, 1], [1, 2], [10, 10], [10, 11]])

        model = KMeans(n_clusters=2, max_iter=100, random_state=42)
        predictions = model.fit_predict(X)

        self.assertEqual(len(predictions), 4)


class TestSimpleNN(unittest.TestCase):
    """Tests for SimpleNN."""

    def test_forward_pass(self):
        """Test forward pass."""
        # Create a simple network
        model = SimpleNN(input_size=10, hidden_sizes=[5], output_size=1)

        # Create random input
        x = torch.randn(1, 10)

        # Forward pass
        output = model(x)
        self.assertEqual(output.shape, (1, 1))

    def test_different_activations(self):
        """Test different activation functions."""
        for activation in ["relu", "sigmoid", "tanh"]:
            model = SimpleNN(
                input_size=5,
                hidden_sizes=[3],
                output_size=1,
                activation=activation,
            )
            x = torch.randn(1, 5)
            output = model(x)
            self.assertEqual(output.shape, (1, 1))

    def test_dropout(self):
        """Test dropout."""
        model = SimpleNN(input_size=10, hidden_sizes=[5], output_size=1, dropout=0.5)
        x = torch.randn(1, 10)

        # In training mode, dropout should be active
        model.train()
        output1 = model(x)

        # In eval mode, dropout should be inactive
        model.eval()
        output2 = model(x)

        # Outputs should be different in training mode due to dropout
        # (This is a probabilistic test, so we just check it runs)
        self.assertEqual(output1.shape, (1, 1))
        self.assertEqual(output2.shape, (1, 1))

    def test_multiple_hidden_layers(self):
        """Test network with multiple hidden layers."""
        model = SimpleNN(
            input_size=10,
            hidden_sizes=[8, 6, 4],
            output_size=2,
        )
        x = torch.randn(1, 10)
        output = model(x)
        self.assertEqual(output.shape, (1, 2))


class TestMLP(unittest.TestCase):
    """Tests for MLP."""

    def test_forward_pass(self):
        """Test forward pass."""
        model = MLP(layer_sizes=[10, 5, 1])
        x = torch.randn(1, 10)
        output = model(x)
        self.assertEqual(output.shape, (1, 1))

    def test_batch_norm(self):
        """Test batch normalization."""
        model = MLP(
            layer_sizes=[10, 5, 1],
            use_batch_norm=True,
        )
        x = torch.randn(2, 10)
        output = model(x)
        self.assertEqual(output.shape, (2, 1))

    def test_leaky_relu(self):
        """Test leaky ReLU activation."""
        model = MLP(
            layer_sizes=[5, 3, 1],
            activation="leaky_relu",
        )
        x = torch.randn(1, 5)
        output = model(x)
        self.assertEqual(output.shape, (1, 1))


if __name__ == "__main__":
    unittest.main()
