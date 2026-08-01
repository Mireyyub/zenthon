"""
K-Means Clustering Model
K-Means clustering implementation for unsupervised learning.
"""

import numpy as np
import random
from typing import Optional, Tuple
from sklearn.metrics import pairwise_distances_argmin_min

from core.logger import logger


class KMeans:
    """
    K-Means clustering algorithm.
    
    Groups data into k clusters by minimizing the within-cluster sum of squares.
    """

    def __init__(
        self,
        n_clusters: int = 8,
        max_iter: int = 300,
        tol: float = 1e-4,
        random_state: Optional[int] = None,
    ):
        """
        Initialize K-Means.

        Args:
            n_clusters: Number of clusters.
            max_iter: Maximum number of iterations.
            tol: Tolerance to declare convergence.
            random_state: Random seed for reproducibility.
        """
        self.n_clusters = n_clusters
        self.max_iter = max_iter
        self.tol = tol
        self.random_state = random_state
        self.centroids = None
        self.labels_ = None
        self.inertia_ = None

        if random_state is not None:
            random.seed(random_state)
            np.random.seed(random_state)

    def fit(self, X: np.ndarray) -> None:
        """
        Fit the K-Means model to the data.

        Args:
            X: Training data (n_samples, n_features).
        """
        n_samples, n_features = X.shape

        # Initialize centroids
        self.centroids = self._init_centroids(X)

        for i in range(self.max_iter):
            # Assign clusters
            labels = self._assign_clusters(X)

            # Update centroids
            new_centroids = np.array([X[labels == k].mean(axis=0) for k in range(self.n_clusters)])

            # Check for convergence
            shift = np.linalg.norm(new_centroids - self.centroids)
            if shift < self.tol:
                break

            self.centroids = new_centroids

        # Final assignment
        self.labels_ = self._assign_clusters(X)
        self.inertia_ = self._compute_inertia(X)

        logger.info(f"K-Means fitted with {self.n_clusters} clusters in {i+1} iterations.")

    def _init_centroids(self, X: np.ndarray) -> np.ndarray:
        """Initialize centroids using k-means++ algorithm."""
        n_samples, n_features = X.shape

        # Randomly select first centroid
        centroids = [X[np.random.randint(n_samples)]]

        for _ in range(1, self.n_clusters):
            # Compute distances to nearest centroid for each point
            dists = np.array([min([np.linalg.norm(x - c) for c in centroids]) for x in X])

            # Choose next centroid with probability proportional to distance squared
            probs = dists ** 2 / np.sum(dists ** 2)
            cumprobs = probs.cumsum()
            r = np.random.rand()

            next_centroid = X[np.searchsorted(cumprobs, r)]
            centroids.append(next_centroid)

        return np.array(centroids)

    def _assign_clusters(self, X: np.ndarray) -> np.ndarray:
        """Assign each data point to the nearest centroid."""
        distances = np.linalg.norm(X[:, np.newaxis] - self.centroids, axis=2)
        return np.argmin(distances, axis=1)

    def _compute_inertia(self, X: np.ndarray) -> float:
        """Compute the sum of squared distances to the nearest centroid."""
        distances = np.linalg.norm(X[:, np.newaxis] - self.centroids, axis=2)
        min_distances = np.min(distances, axis=1)
        return np.sum(min_distances ** 2)

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Predict the closest cluster for each sample in X.

        Args:
            X: Input data (n_samples, n_features).

        Returns:
            Cluster labels (n_samples,).
        """
        if self.centroids is None:
            raise RuntimeError("Model not fitted yet. Call fit() first.")
        return self._assign_clusters(X)

    def transform(self, X: np.ndarray) -> np.ndarray:
        """
        Transform X to a cluster-distance space.

        Args:
            X: Input data (n_samples, n_features).

        Returns:
            Distance to each centroid (n_samples, n_clusters).
        """
        if self.centroids is None:
            raise RuntimeError("Model not fitted yet. Call fit() first.")
        return np.linalg.norm(X[:, np.newaxis] - self.centroids, axis=2)

    def fit_predict(self, X: np.ndarray) -> np.ndarray:
        """
        Fit the model and predict cluster labels.

        Args:
            X: Input data (n_samples, n_features).

        Returns:
            Cluster labels (n_samples,).
        """
        self.fit(X)
        return self.labels_

    def get_centroids(self) -> np.ndarray:
        """Get the current centroids."""
        return self.centroids

    def get_inertia(self) -> float:
        """Get the inertia (sum of squared distances to centroids)."""
        return self.inertia_

    def __repr__(self) -> str:
        return f"KMeans(n_clusters={self.n_clusters}, max_iter={self.max_iter}, tol={self.tol})"
