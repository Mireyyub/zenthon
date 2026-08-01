"""
Data Normalization Module
Provides various normalization techniques for machine learning datasets.
"""

import numpy as np
import pandas as pd
from typing import Union, Optional

from core.logger import logger


class DataNormalizer:
    """Provides methods for normalizing datasets."""

    def __init__(self, verbose: bool = True):
        self.verbose = verbose

    def min_max_normalize(
        self,
        data: Union[pd.DataFrame, np.ndarray],
        feature_range: tuple = (0, 1),
    ) -> Union[pd.DataFrame, np.ndarray]:
        """
        Normalize data to a specified range using min-max scaling.

        Args:
            data: Input data.
            feature_range: Tuple of (min, max) for the target range.

        Returns:
            Normalized data.
        """
        if isinstance(data, pd.DataFrame):
            return self._min_max_normalize_dataframe(data, feature_range)
        elif isinstance(data, np.ndarray):
            return self._min_max_normalize_numpy(data, feature_range)
        else:
            raise ValueError("Data must be a pandas DataFrame or numpy array.")

    def _min_max_normalize_dataframe(
        self,
        data: pd.DataFrame,
        feature_range: tuple,
    ) -> pd.DataFrame:
        """Min-max normalize pandas DataFrame."""
        min_val = data.min()
        max_val = data.max()
        normalized_data = data.copy()

        for col in data.columns:
            if max_val[col] != min_val[col]:
                normalized_data[col] = (
                    (data[col] - min_val[col]) / (max_val[col] - min_val[col])
                ) * (feature_range[1] - feature_range[0]) + feature_range[0]
            else:
                normalized_data[col] = feature_range[0]

        if self.verbose:
            logger.info("Applied Min-Max normalization.")

        return normalized_data

    def _min_max_normalize_numpy(
        self,
        data: np.ndarray,
        feature_range: tuple,
    ) -> np.ndarray:
        """Min-max normalize numpy array."""
        min_val = np.min(data, axis=0)
        max_val = np.max(data, axis=0)
        normalized_data = data.copy()

        for i in range(data.shape[1]):
            if max_val[i] != min_val[i]:
                normalized_data[:, i] = (
                    (data[:, i] - min_val[i]) / (max_val[i] - min_val[i])
                ) * (feature_range[1] - feature_range[0]) + feature_range[0]
            else:
                normalized_data[:, i] = feature_range[0]

        return normalized_data

    def z_score_normalize(
        self,
        data: Union[pd.DataFrame, np.ndarray],
    ) -> Union[pd.DataFrame, np.ndarray]:
        """
        Normalize data using z-score standardization.

        Args:
            data: Input data.

        Returns:
            Normalized data with mean=0 and std=1.
        """
        if isinstance(data, pd.DataFrame):
            return self._z_score_normalize_dataframe(data)
        elif isinstance(data, np.ndarray):
            return self._z_score_normalize_numpy(data)
        else:
            raise ValueError("Data must be a pandas DataFrame or numpy array.")

    def _z_score_normalize_dataframe(self, data: pd.DataFrame) -> pd.DataFrame:
        """Z-score normalize pandas DataFrame."""
        normalized_data = (data - data.mean()) / data.std()
        if self.verbose:
            logger.info("Applied Z-Score normalization.")
        return normalized_data

    def _z_score_normalize_numpy(self, data: np.ndarray) -> np.ndarray:
        """Z-score normalize numpy array."""
        mean = np.mean(data, axis=0)
        std = np.std(data, axis=0)
        normalized_data = (data - mean) / std
        return normalized_data

    def robust_normalize(
        self,
        data: Union[pd.DataFrame, np.ndarray],
    ) -> Union[pd.DataFrame, np.ndarray]:
        """
        Normalize data using robust scaling (median and IQR).

        Args:
            data: Input data.

        Returns:
            Normalized data.
        """
        if isinstance(data, pd.DataFrame):
            return self._robust_normalize_dataframe(data)
        elif isinstance(data, np.ndarray):
            return self._robust_normalize_numpy(data)
        else:
            raise ValueError("Data must be a pandas DataFrame or numpy array.")

    def _robust_normalize_dataframe(self, data: pd.DataFrame) -> pd.DataFrame:
        """Robust normalize pandas DataFrame."""
        median = data.median()
        Q1 = data.quantile(0.25)
        Q3 = data.quantile(0.75)
        IQR = Q3 - Q1

        normalized_data = data.copy()
        for col in data.columns:
            if IQR[col] != 0:
                normalized_data[col] = (data[col] - median[col]) / IQR[col]
            else:
                normalized_data[col] = 0

        if self.verbose:
            logger.info("Applied Robust normalization.")

        return normalized_data

    def _robust_normalize_numpy(self, data: np.ndarray) -> np.ndarray:
        """Robust normalize numpy array."""
        median = np.median(data, axis=0)
        Q1 = np.percentile(data, 25, axis=0)
        Q3 = np.percentile(data, 75, axis=0)
        IQR = Q3 - Q1

        normalized_data = data.copy()
        for i in range(data.shape[1]):
            if IQR[i] != 0:
                normalized_data[:, i] = (data[:, i] - median[i]) / IQR[i]
            else:
                normalized_data[:, i] = 0

        return normalized_data

    def l2_normalize(
        self,
        data: Union[pd.DataFrame, np.ndarray],
    ) -> Union[pd.DataFrame, np.ndarray]:
        """
        Normalize data to unit norm (L2 normalization).

        Args:
            data: Input data.

        Returns:
            Normalized data.
        """
        if isinstance(data, pd.DataFrame):
            return self._l2_normalize_dataframe(data)
        elif isinstance(data, np.ndarray):
            return self._l2_normalize_numpy(data)
        else:
            raise ValueError("Data must be a pandas DataFrame or numpy array.")

    def _l2_normalize_dataframe(self, data: pd.DataFrame) -> pd.DataFrame:
        """L2 normalize pandas DataFrame."""
        normalized_data = data.div(np.sqrt(np.sum(data ** 2, axis=1)), axis=0)
        if self.verbose:
            logger.info("Applied L2 normalization.")
        return normalized_data

    def _l2_normalize_numpy(self, data: np.ndarray) -> np.ndarray:
        """L2 normalize numpy array."""
        norms = np.linalg.norm(data, axis=1)
        normalized_data = data / norms[:, np.newaxis]
        return normalized_data


# Global normalizer instance
normalizer = DataNormalizer()
