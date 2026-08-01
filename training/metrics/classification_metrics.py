"""
Classification Metrics Module
Implements various metrics for classification tasks.
"""

import numpy as np
from typing import Union, Optional, List, Dict, Any
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    roc_auc_score,
    roc_curve,
    precision_recall_curve,
    average_precision_score,
    classification_report,
)

from core.logger import logger


class ClassificationMetrics:
    """
    Collection of classification metrics.
    
    Provides methods to compute various classification metrics.
    """

    def __init__(self, average: str = "binary", zero_division: int = 0):
        """
        Initialize ClassificationMetrics.

        Args:
            average: Type of averaging for multi-class metrics ('binary', 'micro', 'macro', 'weighted').
            zero_division: Value to return when there is a zero division.
        """
        self.average = average
        self.zero_division = zero_division

    def accuracy(
        self,
        y_true: Union[np.ndarray, List[int]],
        y_pred: Union[np.ndarray, List[int]],
    ) -> float:
        """
        Calculate accuracy.

        Args:
            y_true: Ground truth labels.
            y_pred: Predicted labels.

        Returns:
            Accuracy score.
        """
        return accuracy_score(y_true, y_pred)

    def precision(
        self,
        y_true: Union[np.ndarray, List[int]],
        y_pred: Union[np.ndarray, List[int]],
        average: Optional[str] = None,
    ) -> float:
        """
        Calculate precision.

        Args:
            y_true: Ground truth labels.
            y_pred: Predicted labels.
            average: Type of averaging (overrides instance average).

        Returns:
            Precision score.
        """
        avg = average or self.average
        return precision_score(
            y_true, y_pred, average=avg, zero_division=self.zero_division
        )

    def recall(
        self,
        y_true: Union[np.ndarray, List[int]],
        y_pred: Union[np.ndarray, List[int]],
        average: Optional[str] = None,
    ) -> float:
        """
        Calculate recall.

        Args:
            y_true: Ground truth labels.
            y_pred: Predicted labels.
            average: Type of averaging (overrides instance average).

        Returns:
            Recall score.
        """
        avg = average or self.average
        return recall_score(
            y_true, y_pred, average=avg, zero_division=self.zero_division
        )

    def f1(
        self,
        y_true: Union[np.ndarray, List[int]],
        y_pred: Union[np.ndarray, List[int]],
        average: Optional[str] = None,
    ) -> float:
        """
        Calculate F1 score.

        Args:
            y_true: Ground truth labels.
            y_pred: Predicted labels.
            average: Type of averaging (overrides instance average).

        Returns:
            F1 score.
        """
        avg = average or self.average
        return f1_score(
            y_true, y_pred, average=avg, zero_division=self.zero_division
        )

    def confusion_matrix(
        self,
        y_true: Union[np.ndarray, List[int]],
        y_pred: Union[np.ndarray, List[int]],
    ) -> np.ndarray:
        """
        Calculate confusion matrix.

        Args:
            y_true: Ground truth labels.
            y_pred: Predicted labels.

        Returns:
            Confusion matrix.
        """
        return confusion_matrix(y_true, y_pred)

    def roc_auc(
        self,
        y_true: Union[np.ndarray, List[int]],
        y_score: Union[np.ndarray, List[float]],
        average: Optional[str] = None,
        multi_class: str = "raise",
    ) -> float:
        """
        Calculate ROC AUC score.

        Args:
            y_true: Ground truth labels.
            y_score: Predicted probabilities or decision scores.
            average: Type of averaging for multi-class.
            multi_class: Strategy for multi-class ROC AUC ('raise', 'ovr', 'ovo').

        Returns:
            ROC AUC score.
        """
        avg = average or self.average
        return roc_auc_score(
            y_true, y_score, average=avg, multi_class=multi_class
        )

    def average_precision(
        self,
        y_true: Union[np.ndarray, List[int]],
        y_score: Union[np.ndarray, List[float]],
        average: Optional[str] = None,
    ) -> float:
        """
        Calculate average precision score.

        Args:
            y_true: Ground truth labels.
            y_score: Predicted probabilities or decision scores.
            average: Type of averaging (overrides instance average).

        Returns:
            Average precision score.
        """
        avg = average or self.average
        return average_precision_score(
            y_true, y_score, average=avg
        )

    def classification_report(
        self,
        y_true: Union[np.ndarray, List[int]],
        y_pred: Union[np.ndarray, List[int]],
        target_names: Optional[List[str]] = None,
        output_dict: bool = False,
    ) -> Union[str, Dict[str, Any]]:
        """
        Generate classification report.

        Args:
            y_true: Ground truth labels.
            y_pred: Predicted labels.
            target_names: Names of target classes.
            output_dict: If True, return output as dict.

        Returns:
            Classification report as string or dict.
        """
        return classification_report(
            y_true, y_pred, target_names=target_names, output_dict=output_dict
        )

    def compute_all(
        self,
        y_true: Union[np.ndarray, List[int]],
        y_pred: Union[np.ndarray, List[int]],
        y_score: Optional[Union[np.ndarray, List[float]]] = None,
        target_names: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Compute all classification metrics.

        Args:
            y_true: Ground truth labels.
            y_pred: Predicted labels.
            y_score: Predicted probabilities or decision scores.
            target_names: Names of target classes.

        Returns:
            Dictionary containing all metrics.
        """
        metrics = {
            "accuracy": self.accuracy(y_true, y_pred),
            "precision": self.precision(y_true, y_pred),
            "recall": self.recall(y_true, y_pred),
            "f1": self.f1(y_true, y_pred),
            "confusion_matrix": self.confusion_matrix(y_true, y_pred),
        }

        if y_score is not None:
            metrics["roc_auc"] = self.roc_auc(y_true, y_score)
            metrics["average_precision"] = self.average_precision(y_true, y_score)

        if target_names is not None:
            metrics["classification_report"] = self.classification_report(
                y_true, y_pred, target_names=target_names, output_dict=True
            )

        return metrics


class BinaryClassificationMetrics(ClassificationMetrics):
    """
    Classification metrics for binary classification.
    """

    def __init__(self):
        super(BinaryClassificationMetrics, self).__init__(average="binary")

    def sensitivity(
        self,
        y_true: Union[np.ndarray, List[int]],
        y_pred: Union[np.ndarray, List[int]],
    ) -> float:
        """
        Calculate sensitivity (true positive rate).

        Args:
            y_true: Ground truth labels.
            y_pred: Predicted labels.

        Returns:
            Sensitivity score.
        """
        return self.recall(y_true, y_pred, average="binary")

    def specificity(
        self,
        y_true: Union[np.ndarray, List[int]],
        y_pred: Union[np.ndarray, List[int]],
    ) -> float:
        """
        Calculate specificity (true negative rate).

        Args:
            y_true: Ground truth labels.
            y_pred: Predicted labels.

        Returns:
            Specificity score.
        """
        tn, fp, fn, tp = self.confusion_matrix(y_true, y_pred).ravel()
        return tn / (tn + fp) if (tn + fp) > 0 else 0.0

    def false_positive_rate(
        self,
        y_true: Union[np.ndarray, List[int]],
        y_pred: Union[np.ndarray, List[int]],
    ) -> float:
        """
        Calculate false positive rate.

        Args:
            y_true: Ground truth labels.
            y_pred: Predicted labels.

        Returns:
            False positive rate.
        """
        return 1.0 - self.specificity(y_true, y_pred)

    def false_negative_rate(
        self,
        y_true: Union[np.ndarray, List[int]],
        y_pred: Union[np.ndarray, List[int]],
    ) -> float:
        """
        Calculate false negative rate.

        Args:
            y_true: Ground truth labels.
            y_pred: Predicted labels.

        Returns:
            False negative rate.
        """
        return 1.0 - self.sensitivity(y_true, y_pred)


class MultiClassClassificationMetrics(ClassificationMetrics):
    """
    Classification metrics for multi-class classification.
    """

    def __init__(self, average: str = "macro"):
        super(MultiClassClassificationMetrics, self).__init__(average=average)

    def compute_class_metrics(
        self,
        y_true: Union[np.ndarray, List[int]],
        y_pred: Union[np.ndarray, List[int]],
    ) -> Dict[str, Dict[str, float]]:
        """
        Compute metrics for each class.

        Args:
            y_true: Ground truth labels.
            y_pred: Predicted labels.

        Returns:
            Dictionary with metrics for each class.
        """
        classes = np.unique(np.concatenate([y_true, y_pred]))
        class_metrics = {}

        for cls in classes:
            y_true_cls = (y_true == cls).astype(int)
            y_pred_cls = (y_pred == cls).astype(int)

            class_metrics[int(cls)] = {
                "precision": precision_score(
                    y_true_cls, y_pred_cls, zero_division=self.zero_division
                ),
                "recall": recall_score(
                    y_true_cls, y_pred_cls, zero_division=self.zero_division
                ),
                "f1": f1_score(
                    y_true_cls, y_pred_cls, zero_division=self.zero_division
                ),
                "count": int(np.sum(y_true_cls)),
            }

        return class_metrics
