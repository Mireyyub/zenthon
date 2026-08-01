"""
Linear Regression Model
Simple linear regression implementation for supervised learning.
"""

import numpy as np
from typing import Optional, Tuple

from core.logger import logger


class LinearRegression:
    """
    Linear Regression model using ordinary least squares.
    
    Attributes:
        weights: Model weights (coefficients).
        bias: Model bias (intercept).
    """

    def __init__(self, fit_intercept: bool = True):
        """
        Initialize Linear Regression model.

        Args:
            fit_intercept: Whether to calculate the intercept (bias).
        """
        self.weights = None
        self.bias = 0.0 if fit_intercept else None
        self.fit_intercept = fit_intercept

    def fit(
        self,
        X: np.ndarray,
        y: np.ndarray,
        max_iter: int = 1000,
        learning_rate: float = 0.01,
        method: str = "normal",
    ) -> None:
        """
        Fit the linear regression model to the training data.

        Args:
            X: Training data features (n_samples, n_features).
            y: Training data targets (n_samples,).
            max_iter: Maximum number of iterations (for gradient descent).
            learning_rate: Learning rate (for gradient descent).
            method: Fitting method ('normal' or 'gradient').
        """
        if X.shape[0] != y.shape[0]:
            raise ValueError(f"X and y must have the same number of samples. Got {X.shape[0]} and {y.shape[0]}.")

        n_samples, n_features = X.shape

        if method == "normal":
            self._fit_normal_equation(X, y)
        elif method == "gradient":
            self._fit_gradient_descent(X, y, max_iter, learning_rate)
        else:
            raise ValueError(f"Unknown method: {method}")

        logger.info(f"Linear Regression model fitted with {n_samples} samples and {n_features} features.")

    def _fit_normal_equation(self, X: np.ndarray, y: np.ndarray) -> None:
        """Fit using the normal equation (closed-form solution)."""
        # Add bias column if fit_intercept is True
        if self.fit_intercept:
            X = np.column_stack([np.ones(X.shape[0]), X])

        # Calculate weights using normal equation: (X^T X)^-1 X^T y
        XtX = np.dot(X.T, X)
        XtX_inv = np.linalg.inv(XtX)
        Xty = np.dot(X.T, y)
        weights = np.dot(XtX_inv, Xty)

        if self.fit_intercept:
            self.bias = weights[0]
            self.weights = weights[1:]
        else:
            self.weights = weights

    def _fit_gradient_descent(
        self,
        X: np.ndarray,
        y: np.ndarray,
        max_iter: int,
        learning_rate: float,
    ) -> None:
        """Fit using gradient descent optimization."""
        n_samples, n_features = X.shape

        # Initialize weights
        self.weights = np.zeros(n_features)
        if self.fit_intercept:
            self.bias = 0.0

        # Gradient descent
        for i in range(max_iter):
            # Predictions
            y_pred = self._predict(X)

            # Compute gradients
            error = y_pred - y
            d_weights = np.dot(X.T, error) / n_samples
            d_bias = np.sum(error) / n_samples if self.fit_intercept else 0.0

            # Update weights
            self.weights -= learning_rate * d_weights
            if self.fit_intercept:
                self.bias -= learning_rate * d_bias

            # Log progress
            if i % 100 == 0:
                loss = np.mean(error ** 2)
                logger.debug(f"Iteration {i}, Loss: {loss:.4f}")

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Predict using the linear regression model.

        Args:
            X: Input data (n_samples, n_features).

        Returns:
            Predicted values (n_samples,).
        """
        return self._predict(X)

    def _predict(self, X: np.ndarray) -> np.ndarray:
        """Internal prediction method."""
        if self.weights is None:
            raise RuntimeError("Model not fitted yet. Call fit() first.")

        y_pred = np.dot(X, self.weights)
        if self.fit_intercept:
            y_pred += self.bias
        return y_pred

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """
        Calculate the R-squared score of the model.

        Args:
            X: Test data features.
            y: Test data targets.

        Returns:
            R-squared score.
        """
        y_pred = self.predict(X)
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        return 1 - (ss_res / ss_tot)

    def get_coefficients(self) -> Tuple[Optional[float], Optional[np.ndarray]]:
        """
        Get the model coefficients.

        Returns:
            Tuple of (bias, weights).
        """
        return self.bias, self.weights

    def __repr__(self) -> str:
        return f"LinearRegression(fit_intercept={self.fit_intercept}, weights={self.weights}, bias={self.bias})"
