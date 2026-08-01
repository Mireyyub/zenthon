"""
Statistics Utilities Module
Provides statistical functions and operations.
"""

import numpy as np
from typing import Union, Optional, List, Dict, Any
from scipy import stats

from core.logger import logger


class StatisticsUtils:
    """
    Collection of statistical utilities.
    """

    @staticmethod
    def mean(
        data: np.ndarray,
        axis: Optional[int] = None,
    ) -> float:
        """
        Compute the arithmetic mean.

        Args:
            data: Input data.
            axis: Axis along which to compute the mean.

        Returns:
            Mean value.
        """
        return np.mean(data, axis=axis)

    @staticmethod
    def median(
        data: np.ndarray,
        axis: Optional[int] = None,
    ) -> float:
        """
        Compute the median.

        Args:
            data: Input data.
            axis: Axis along which to compute the median.

        Returns:
            Median value.
        """
        return np.median(data, axis=axis)

    @staticmethod
    def std(
        data: np.ndarray,
        axis: Optional[int] = None,
        ddof: int = 0,
    ) -> float:
        """
        Compute the standard deviation.

        Args:
            data: Input data.
            axis: Axis along which to compute the standard deviation.
            ddof: Delta degrees of freedom.

        Returns:
            Standard deviation.
        """
        return np.std(data, axis=axis, ddof=ddof)

    @staticmethod
    def var(
        data: np.ndarray,
        axis: Optional[int] = None,
        ddof: int = 0,
    ) -> float:
        """
        Compute the variance.

        Args:
            data: Input data.
            axis: Axis along which to compute the variance.
            ddof: Delta degrees of freedom.

        Returns:
            Variance.
        """
        return np.var(data, axis=axis, ddof=ddof)

    @staticmethod
    def min(
        data: np.ndarray,
        axis: Optional[int] = None,
    ) -> float:
        """
        Compute the minimum value.

        Args:
            data: Input data.
            axis: Axis along which to compute the minimum.

        Returns:
            Minimum value.
        """
        return np.min(data, axis=axis)

    @staticmethod
    def max(
        data: np.ndarray,
        axis: Optional[int] = None,
    ) -> float:
        """
        Compute the maximum value.

        Args:
            data: Input data.
            axis: Axis along which to compute the maximum.

        Returns:
            Maximum value.
        """
        return np.max(data, axis=axis)

    @staticmethod
    def range(
        data: np.ndarray,
    ) -> float:
        """
        Compute the range (max - min).

        Args:
            data: Input data.

        Returns:
            Range value.
        """
        return np.max(data) - np.min(data)

    @staticmethod
    def quantile(
        data: np.ndarray,
        q: float,
        axis: Optional[int] = None,
    ) -> float:
        """
        Compute a quantile.

        Args:
            data: Input data.
            q: Quantile to compute (between 0 and 1).
            axis: Axis along which to compute the quantile.

        Returns:
            Quantile value.
        """
        return np.quantile(data, q, axis=axis)

    @staticmethod
    def iqr(
        data: np.ndarray,
        axis: Optional[int] = None,
    ) -> float:
        """
        Compute the interquartile range (IQR).

        Args:
            data: Input data.
            axis: Axis along which to compute the IQR.

        Returns:
            IQR value.
        """
        q75 = np.quantile(data, 0.75, axis=axis)
        q25 = np.quantile(data, 0.25, axis=axis)
        return q75 - q25

    @staticmethod
    def skewness(
        data: np.ndarray,
        axis: Optional[int] = None,
        bias: bool = True,
    ) -> float:
        """
        Compute the skewness.

        Args:
            data: Input data.
            axis: Axis along which to compute the skewness.
            bias: If False, the calculations are corrected for statistical bias.

        Returns:
            Skewness value.
        """
        return stats.skew(data, axis=axis, bias=bias)

    @staticmethod
    def kurtosis(
        data: np.ndarray,
        axis: Optional[int] = None,
        fisher: bool = True,
        bias: bool = True,
    ) -> float:
        """
        Compute the kurtosis.

        Args:
            data: Input data.
            axis: Axis along which to compute the kurtosis.
            fisher: If True, Fisher's definition is used (normal ==> 0.0).
            bias: If False, the calculations are corrected for statistical bias.

        Returns:
            Kurtosis value.
        """
        return stats.kurtosis(data, axis=axis, fisher=fisher, bias=bias)

    @staticmethod
    def correlation(
        x: np.ndarray,
        y: np.ndarray,
    ) -> float:
        """
        Compute the Pearson correlation coefficient.

        Args:
            x: First variable.
            y: Second variable.

        Returns:
            Correlation coefficient (between -1 and 1).
        """
        return np.corrcoef(x, y)[0, 1]

    @staticmethod
    def correlation_matrix(
        data: np.ndarray,
    ) -> np.ndarray:
        """
        Compute the correlation matrix.

        Args:
            data: Input data (n_samples, n_features).

        Returns:
            Correlation matrix (n_features, n_features).
        """
        return np.corrcoef(data, rowvar=False)

    @staticmethod
    def covariance(
        x: np.ndarray,
        y: np.ndarray,
    ) -> float:
        """
        Compute the covariance.

        Args:
            x: First variable.
            y: Second variable.

        Returns:
            Covariance value.
        """
        return np.cov(x, y)[0, 1]

    @staticmethod
    def covariance_matrix(
        data: np.ndarray,
        rowvar: bool = True,
    ) -> np.ndarray:
        """
        Compute the covariance matrix.

        Args:
            data: Input data (n_samples, n_features).
            rowvar: If True, each row represents a variable.

        Returns:
            Covariance matrix.
        """
        return np.cov(data, rowvar=rowvar)

    @staticmethod
    def z_score(
        data: np.ndarray,
        axis: Optional[int] = None,
    ) -> np.ndarray:
        """
        Compute z-scores (standard scores).

        Args:
            data: Input data.
            axis: Axis along which to compute z-scores.

        Returns:
            Z-scores.
        """
        mean = np.mean(data, axis=axis, keepdims=True)
        std = np.std(data, axis=axis, keepdims=True, ddof=1)
        return (data - mean) / std

    @staticmethod
    def percentile(
        data: np.ndarray,
        percentile: float,
        axis: Optional[int] = None,
    ) -> float:
        """
        Compute a percentile.

        Args:
            data: Input data.
            percentile: Percentile to compute (between 0 and 100).
            axis: Axis along which to compute the percentile.

        Returns:
            Percentile value.
        """
        return np.percentile(data, percentile, axis=axis)

    @staticmethod
    def histogram(
        data: np.ndarray,
        bins: int = 10,
        range: Optional[tuple] = None,
    ) -> tuple:
        """
        Compute histogram.

        Args:
            data: Input data.
            bins: Number of bins.
            range: Range of the bins.

        Returns:
            Tuple of (hist, bin_edges).
        """
        return np.histogram(data, bins=bins, range=range)

    @staticmethod
    def mode(
        data: np.ndarray,
        axis: Optional[int] = None,
    ) -> tuple:
        """
        Compute the mode.

        Args:
            data: Input data.
            axis: Axis along which to compute the mode.

        Returns:
            Tuple of (values, counts).
        """
        return stats.mode(data, axis=axis)

    @staticmethod
    def geometric_mean(
        data: np.ndarray,
        axis: Optional[int] = None,
    ) -> float:
        """
        Compute the geometric mean.

        Args:
            data: Input data.
            axis: Axis along which to compute the geometric mean.

        Returns:
            Geometric mean.
        """
        return stats.gmean(data, axis=axis)

    @staticmethod
    def harmonic_mean(
        data: np.ndarray,
        axis: Optional[int] = None,
    ) -> float:
        """
        Compute the harmonic mean.

        Args:
            data: Input data.
            axis: Axis along which to compute the harmonic mean.

        Returns:
            Harmonic mean.
        """
        return stats.hmean(data, axis=axis)

    @staticmethod
    def trimmed_mean(
        data: np.ndarray,
        proportiontocut: float = 0.1,
        axis: Optional[int] = None,
    ) -> float:
        """
        Compute the trimmed mean.

        Args:
            data: Input data.
            proportiontocut: Proportion to cut from each end.
            axis: Axis along which to compute the trimmed mean.

        Returns:
            Trimmed mean.
        """
        return stats.trim_mean(data, proportiontocut=proportiontocut, axis=axis)

    @staticmethod
    def describe(
        data: np.ndarray,
    ) -> Dict[str, Any]:
        """
        Generate descriptive statistics.

        Args:
            data: Input data.

        Returns:
            Dictionary containing descriptive statistics.
        """
        return {
            "count": len(data),
            "mean": float(np.mean(data)),
            "std": float(np.std(data, ddof=1)),
            "min": float(np.min(data)),
            "25%": float(np.percentile(data, 25)),
            "50%": float(np.median(data)),
            "75%": float(np.percentile(data, 75)),
            "max": float(np.max(data)),
            "range": float(np.max(data) - np.min(data)),
            "skewness": float(stats.skew(data)),
            "kurtosis": float(stats.kurtosis(data)),
        }

    @staticmethod
    def ttest_ind(
        a: np.ndarray,
        b: np.ndarray,
        equal_var: bool = True,
    ) -> tuple:
        """
        Perform independent t-test.

        Args:
            a: First sample.
            b: Second sample.
            equal_var: If True, perform standard independent 2 sample test.

        Returns:
            Tuple of (t-statistic, p-value).
        """
        return stats.ttest_ind(a, b, equal_var=equal_var)

    @staticmethod
    def ttest_1samp(
        a: np.ndarray,
        popmean: float,
    ) -> tuple:
        """
        Perform one-sample t-test.

        Args:
            a: Sample.
            popmean: Expected population mean.

        Returns:
            Tuple of (t-statistic, p-value).
        """
        return stats.ttest_1samp(a, popmean)

    @staticmethod
    def chi2_contingency(
        observed: np.ndarray,
    ) -> tuple:
        """
        Perform chi-squared test for contingency table.

        Args:
            observed: Contingency table.

        Returns:
            Tuple of (chi2, p-value, dof, expected).
        """
        return stats.chi2_contingency(observed)

    @staticmethod
    def norm_test(
        data: np.ndarray,
    ) -> tuple:
        """
        Test whether a sample comes from a normal distribution.

        Args:
            data: Sample data.

        Returns:
            Tuple of (statistic, p-value).
        """
        return stats.normaltest(data)
