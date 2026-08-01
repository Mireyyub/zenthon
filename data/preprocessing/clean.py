"""
Data Cleaning Module
Handles missing values, duplicates, and outliers in datasets.
"""

import numpy as np
import pandas as pd
from typing import Union, Optional, List

from core.logger import logger


class DataCleaner:
    """Provides methods for cleaning datasets."""

    def __init__(self, verbose: bool = True):
        self.verbose = verbose

    def handle_missing_values(
        self,
        data: Union[pd.DataFrame, np.ndarray],
        strategy: str = "drop",
        fill_value: Optional[Union[float, str]] = None,
    ) -> Union[pd.DataFrame, np.ndarray]:
        """
        Handle missing values in the dataset.

        Args:
            data: Input data (DataFrame or numpy array).
            strategy: Strategy to handle missing values ('drop', 'fill', 'interpolate').
            fill_value: Value to use when strategy is 'fill'.

        Returns:
            Cleaned data.
        """
        if isinstance(data, np.ndarray):
            return self._handle_missing_numpy(data, strategy, fill_value)
        elif isinstance(data, pd.DataFrame):
            return self._handle_missing_dataframe(data, strategy, fill_value)
        else:
            raise ValueError("Data must be a pandas DataFrame or numpy array.")

    def _handle_missing_numpy(
        self,
        data: np.ndarray,
        strategy: str,
        fill_value: Optional[Union[float, str]],
    ) -> np.ndarray:
        """Handle missing values in numpy array."""
        if strategy == "drop":
            # For numpy, we can only drop rows/columns with all NaN
            mask = ~np.isnan(data).any(axis=1)
            cleaned_data = data[mask]
            if self.verbose:
                dropped_rows = data.shape[0] - cleaned_data.shape[0]
                logger.info(f"Dropped {dropped_rows} rows with missing values.")
            return cleaned_data

        elif strategy == "fill":
            if fill_value is None:
                fill_value = 0
            cleaned_data = np.where(np.isnan(data), fill_value, data)
            if self.verbose:
                filled_count = np.isnan(data).sum()
                logger.info(f"Filled {filled_count} missing values with {fill_value}.")
            return cleaned_data

        elif strategy == "interpolate":
            # Linear interpolation for numpy arrays
            cleaned_data = data.copy()
            for i in range(data.shape[1]):
                mask = np.isnan(cleaned_data[:, i])
                if mask.any():
                    x = np.arange(data.shape[0])
                    cleaned_data[:, i] = np.interp(
                        x, x[~mask], cleaned_data[~mask, i], left=np.nan, right=np.nan
                    )
            return cleaned_data

        else:
            raise ValueError(f"Unknown strategy: {strategy}")

    def _handle_missing_dataframe(
        self,
        data: pd.DataFrame,
        strategy: str,
        fill_value: Optional[Union[float, str]],
    ) -> pd.DataFrame:
        """Handle missing values in pandas DataFrame."""
        if strategy == "drop":
            cleaned_data = data.dropna()
            if self.verbose:
                dropped_rows = data.shape[0] - cleaned_data.shape[0]
                logger.info(f"Dropped {dropped_rows} rows with missing values.")
            return cleaned_data

        elif strategy == "fill":
            if fill_value is None:
                fill_value = data.mean().to_dict()
            cleaned_data = data.fillna(fill_value)
            if self.verbose:
                filled_count = data.isna().sum().sum()
                logger.info(f"Filled {filled_count} missing values.")
            return cleaned_data

        elif strategy == "interpolate":
            cleaned_data = data.interpolate()
            if self.verbose:
                filled_count = data.isna().sum().sum() - cleaned_data.isna().sum().sum()
                logger.info(f"Interpolated {filled_count} missing values.")
            return cleaned_data

        else:
            raise ValueError(f"Unknown strategy: {strategy}")

    def remove_duplicates(
        self,
        data: Union[pd.DataFrame, np.ndarray],
        subset: Optional[List[str]] = None,
    ) -> Union[pd.DataFrame, np.ndarray]:
        """
        Remove duplicate rows from the dataset.

        Args:
            data: Input data.
            subset: Columns to consider for identifying duplicates (DataFrame only).

        Returns:
            Data with duplicates removed.
        """
        if isinstance(data, pd.DataFrame):
            cleaned_data = data.drop_duplicates(subset=subset)
            if self.verbose:
                duplicates = data.shape[0] - cleaned_data.shape[0]
                logger.info(f"Removed {duplicates} duplicate rows.")
            return cleaned_data

        elif isinstance(data, np.ndarray):
            # For numpy arrays, we can only check for exact duplicate rows
            unique_rows = np.unique(data, axis=0)
            if self.verbose:
                duplicates = data.shape[0] - unique_rows.shape[0]
                logger.info(f"Removed {duplicates} duplicate rows.")
            return unique_rows

        else:
            raise ValueError("Data must be a pandas DataFrame or numpy array.")

    def handle_outliers(
        self,
        data: Union[pd.DataFrame, np.ndarray],
        method: str = "zscore",
        threshold: float = 3.0,
    ) -> Union[pd.DataFrame, np.ndarray]:
        """
        Handle outliers in the dataset.

        Args:
            data: Input data.
            method: Method for outlier detection ('zscore', 'iqr').
            threshold: Threshold for outlier detection.

        Returns:
            Data with outliers handled.
        """
        if isinstance(data, pd.DataFrame):
            return self._handle_outliers_dataframe(data, method, threshold)
        elif isinstance(data, np.ndarray):
            return self._handle_outliers_numpy(data, method, threshold)
        else:
            raise ValueError("Data must be a pandas DataFrame or numpy array.")

    def _handle_outliers_dataframe(
        self,
        data: pd.DataFrame,
        method: str,
        threshold: float,
    ) -> pd.DataFrame:
        """Handle outliers in pandas DataFrame."""
        cleaned_data = data.copy()

        if method == "zscore":
            z_scores = np.abs((cleaned_data - cleaned_data.mean()) / cleaned_data.std())
            cleaned_data[z_scores > threshold] = np.nan

        elif method == "iqr":
            Q1 = cleaned_data.quantile(0.25)
            Q3 = cleaned_data.quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            cleaned_data[(cleaned_data < lower_bound) | (cleaned_data > upper_bound)] = np.nan

        else:
            raise ValueError(f"Unknown method: {method}")

        # Fill NaN values created by outlier removal with median
        cleaned_data = cleaned_data.fillna(cleaned_data.median())

        if self.verbose:
            outliers_removed = (data != cleaned_data).sum().sum()
            logger.info(f"Handled {outliers_removed} outliers using {method} method.")

        return cleaned_data

    def _handle_outliers_numpy(
        self,
        data: np.ndarray,
        method: str,
        threshold: float,
    ) -> np.ndarray:
        """Handle outliers in numpy array."""
        cleaned_data = data.copy()

        if method == "zscore":
            z_scores = np.abs((cleaned_data - np.nanmean(cleaned_data, axis=0)) / np.nanstd(cleaned_data, axis=0))
            cleaned_data[z_scores > threshold] = np.nan

        elif method == "iqr":
            Q1 = np.nanpercentile(cleaned_data, 25, axis=0)
            Q3 = np.nanpercentile(cleaned_data, 75, axis=0)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            cleaned_data[(cleaned_data < lower_bound) | (cleaned_data > upper_bound)] = np.nan

        else:
            raise ValueError(f"Unknown method: {method}")

        # Fill NaN values with median
        for i in range(cleaned_data.shape[1]):
            col_median = np.nanmedian(cleaned_data[:, i])
            cleaned_data[np.isnan(cleaned_data[:, i]), i] = col_median

        return cleaned_data


# Global cleaner instance
cleaner = DataCleaner()
