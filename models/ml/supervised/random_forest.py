"""
Random Forest Model
Random Forest classifier and regressor implementation.
"""

import numpy as np
import random
from typing import List, Optional, Union
from collections import Counter

from core.logger import logger


class DecisionTree:
    """Decision Tree base class."""

    def __init__(
        self,
        max_depth: Optional[int] = None,
        min_samples_split: int = 2,
        min_samples_leaf: int = 1,
    ):
        """
        Initialize Decision Tree.

        Args:
            max_depth: Maximum depth of the tree.
            min_samples_split: Minimum number of samples required to split a node.
            min_samples_leaf: Minimum number of samples required at a leaf node.
        """
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.min_samples_leaf = min_samples_leaf
        self.tree = None

    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        """Fit the decision tree to the training data."""
        self.tree = self._grow_tree(X, y)

    def _grow_tree(self, X: np.ndarray, y: np.ndarray, depth: int = 0) -> dict:
        """Recursively grow the decision tree."""
        n_samples, n_features = X.shape
        n_classes = len(np.unique(y))

        # Stopping conditions
        if (self.max_depth is not None and depth >= self.max_depth) or \
           (n_samples < self.min_samples_split) or \
           (n_classes == 1):
            leaf_value = self._most_common_label(y)
            return {"leaf": True, "value": leaf_value, "samples": n_samples}

        # Find best split
        best_split = self._find_best_split(X, y, n_features)
        if best_split["gain"] <= 0:
            leaf_value = self._most_common_label(y)
            return {"leaf": True, "value": leaf_value, "samples": n_samples}

        # Split the data
        left_idxs, right_idxs = self._split(X, best_split["feature"], best_split["threshold"])
        left = self._grow_tree(X[left_idxs], y[left_idxs], depth + 1)
        right = self._grow_tree(X[right_idxs], y[right_idxs], depth + 1)

        return {
            "leaf": False,
            "feature": best_split["feature"],
            "threshold": best_split["threshold"],
            "left": left,
            "right": right,
            "samples": n_samples,
        }

    def _find_best_split(self, X: np.ndarray, y: np.ndarray, n_features: int) -> dict:
        """Find the best split for a node."""
        best_gain = -1
        best_split = {"feature": None, "threshold": None, "gain": -1}

        # Sample a subset of features (for Random Forest)
        feature_idxs = random.sample(range(n_features), int(np.sqrt(n_features)))

        for feature_idx in feature_idxs:
            thresholds = np.unique(X[:, feature_idx])
            for threshold in thresholds:
                gain = self._information_gain(X, y, feature_idx, threshold)
                if gain > best_gain:
                    best_gain = gain
                    best_split = {
                        "feature": feature_idx,
                        "threshold": threshold,
                        "gain": gain,
                    }

        return best_split

    def _information_gain(self, X: np.ndarray, y: np.ndarray, feature_idx: int, threshold: float) -> float:
        """Calculate information gain for a split."""
        # Parent entropy
        parent_entropy = self._entropy(y)

        # Split the data
        left_idxs, right_idxs = self._split(X, feature_idx, threshold)

        if len(left_idxs) == 0 or len(right_idxs) == 0:
            return 0

        # Weighted child entropy
        n = len(y)
        n_left, n_right = len(left_idxs), len(right_idxs)
        child_entropy = (n_left / n) * self._entropy(y[left_idxs]) + \
                        (n_right / n) * self._entropy(y[right_idxs])

        # Information gain
        return parent_entropy - child_entropy

    def _split(self, X: np.ndarray, feature_idx: int, threshold: float) -> tuple:
        """Split the data based on a feature and threshold."""
        left_idxs = np.where(X[:, feature_idx] <= threshold)[0]
        right_idxs = np.where(X[:, feature_idx] > threshold)[0]
        return left_idxs, right_idxs

    def _entropy(self, y: np.ndarray) -> float:
        """Calculate entropy of a label distribution."""
        hist = np.bincount(y)
        ps = hist / len(y)
        return -np.sum([p * np.log2(p) for p in ps if p > 0])

    def _most_common_label(self, y: np.ndarray) -> int:
        """Get the most common label in a set."""
        counter = Counter(y)
        return counter.most_common(1)[0][0]

    def predict_sample(self, x: np.ndarray, node: dict = None) -> int:
        """Predict a single sample."""
        if node is None:
            node = self.tree

        if node["leaf"]:
            return node["value"]

        if x[node["feature"]] <= node["threshold"]:
            return self.predict_sample(x, node["left"])
        else:
            return self.predict_sample(x, node["right"])

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict class labels for input samples."""
        return np.array([self.predict_sample(x) for x in X])


class RandomForest:
    """
    Random Forest classifier.
    
    An ensemble learning method that operates by constructing multiple decision trees.
    """

    def __init__(
        self,
        n_estimators: int = 100,
        max_depth: Optional[int] = None,
        min_samples_split: int = 2,
        min_samples_leaf: int = 1,
        max_features: Optional[int] = None,
        random_state: Optional[int] = None,
    ):
        """
        Initialize Random Forest.

        Args:
            n_estimators: Number of trees in the forest.
            max_depth: Maximum depth of each tree.
            min_samples_split: Minimum number of samples required to split a node.
            min_samples_leaf: Minimum number of samples required at a leaf node.
            max_features: Number of features to consider for the best split.
            random_state: Random seed for reproducibility.
        """
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.min_samples_leaf = min_samples_leaf
        self.max_features = max_features
        self.random_state = random_state
        self.trees = []

        if random_state is not None:
            random.seed(random_state)
            np.random.seed(random_state)

    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        """
        Fit the random forest to the training data.

        Args:
            X: Training data features (n_samples, n_features).
            y: Training data targets (n_samples,).
        """
        self.trees = []
        n_samples = X.shape[0]

        for _ in range(self.n_estimators):
            # Bootstrap sample
            idxs = np.random.choice(n_samples, n_samples, replace=True)
            X_sample, y_sample = X[idxs], y[idxs]

            # Create and train tree
            tree = DecisionTree(
                max_depth=self.max_depth,
                min_samples_split=self.min_samples_split,
                min_samples_leaf=self.min_samples_leaf,
            )
            tree.fit(X_sample, y_sample)
            self.trees.append(tree)

        logger.info(f"Random Forest fitted with {self.n_estimators} trees.")

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Predict class labels for input samples.

        Args:
            X: Input data (n_samples, n_features).

        Returns:
            Predicted class labels (n_samples,).
        """
        predictions = np.array([tree.predict(X) for tree in self.trees])
        # Majority vote
        return np.array([Counter(predictions[:, i]).most_common(1)[0][0] for i in range(X.shape[0])])

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Predict class probabilities for input samples.

        Args:
            X: Input data (n_samples, n_features).

        Returns:
            Probability estimates (n_samples, n_classes).
        """
        predictions = np.array([tree.predict(X) for tree in self.trees])
        n_samples = X.shape[0]
        classes = np.unique(predictions)
        proba = np.zeros((n_samples, len(classes)))

        for i, c in enumerate(classes):
            proba[:, i] = np.sum(predictions == c, axis=0) / self.n_estimators

        return proba

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """
        Calculate the accuracy of the model.

        Args:
            X: Test data features.
            y: Test data targets.

        Returns:
            Accuracy score.
        """
        y_pred = self.predict(X)
        return np.mean(y_pred == y)

    def __repr__(self) -> str:
        return f"RandomForest(n_estimators={self.n_estimators}, max_depth={self.max_depth})"
