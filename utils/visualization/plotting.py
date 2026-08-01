"""
Plotting Utilities Module
Provides data visualization functions using Matplotlib and Seaborn.
"""

import os
import numpy as np
import pandas as pd
from typing import Optional, Dict, Any, List, Tuple, Union
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for saving plots
import matplotlib.pyplot as plt
import seaborn as sns

from core.logger import logger
from core.config import config


class Plotter:
    """
    Collection of plotting utilities.
    """

    def __init__(self):
        """Initialize Plotter."""
        # Set default style
        plt.style.use('seaborn-v0_8-whitegrid')
        sns.set_palette("husl")

        # Create output directory if it doesn't exist
        self.output_dir = os.path.join(config.path.base_dir, "plots")
        os.makedirs(self.output_dir, exist_ok=True)

    def save_plot(
        self,
        filename: Optional[str] = None,
        dpi: int = 300,
        bbox_inches: str = "tight",
    ) -> str:
        """
        Save the current plot to a file.

        Args:
            filename: Name of the file (without extension).
            dpi: Dots per inch.
            bbox_inches: Bounding box in inches.

        Returns:
            Path to the saved file.
        """
        if filename is None:
            filename = f"plot_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}"

        if not filename.endswith(".png"):
            filename += ".png"

        filepath = os.path.join(self.output_dir, filename)
        plt.savefig(filepath, dpi=dpi, bbox_inches=bbox_inches)
        plt.close()

        logger.info(f"Plot saved to {filepath}")
        return filepath

    def show_plot(self) -> None:
        """Show the current plot."""
        plt.show()

    def close_plot(self) -> None:
        """Close the current plot."""
        plt.close()

    # Line plots
    def plot_line(
        self,
        x: Union[np.ndarray, pd.Series, List[float]],
        y: Optional[Union[np.ndarray, pd.Series, List[float]]] = None,
        title: str = "Line Plot",
        xlabel: str = "X",
        ylabel: str = "Y",
        label: Optional[str] = None,
        color: Optional[str] = None,
        linewidth: float = 2.0,
        figsize: Tuple[int, int] = (10, 6),
        save: bool = False,
        filename: Optional[str] = None,
        **kwargs,
    ) -> Optional[str]:
        """
        Create a line plot.

        Args:
            x: X-axis data.
            y: Y-axis data (if None, use x as y and create index for x).
            title: Plot title.
            xlabel: X-axis label.
            ylabel: Y-axis label.
            label: Line label.
            color: Line color.
            linewidth: Line width.
            figsize: Figure size.
            save: Whether to save the plot.
            filename: Filename for saving.
            **kwargs: Additional arguments for plt.plot.

        Returns:
            Path to saved file if save=True, else None.
        """
        plt.figure(figsize=figsize)

        if y is None:
            y = x
            x = np.arange(len(y))

        plt.plot(x, y, label=label, color=color, linewidth=linewidth, **kwargs)

        if label:
            plt.legend()

        plt.title(title)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)

        if save:
            return self.save_plot(filename)
        return None

    def plot_multiple_lines(
        self,
        data: Dict[str, Union[np.ndarray, pd.Series, List[float]]],
        title: str = "Multiple Line Plot",
        xlabel: str = "X",
        ylabel: str = "Y",
        figsize: Tuple[int, int] = (10, 6),
        save: bool = False,
        filename: Optional[str] = None,
        **kwargs,
    ) -> Optional[str]:
        """
        Create a plot with multiple lines.

        Args:
            data: Dictionary of {label: y_data}.
            title: Plot title.
            xlabel: X-axis label.
            ylabel: Y-axis label.
            figsize: Figure size.
            save: Whether to save the plot.
            filename: Filename for saving.
            **kwargs: Additional arguments for plt.plot.

        Returns:
            Path to saved file if save=True, else None.
        """
        plt.figure(figsize=figsize)

        for label, y in data.items():
            x = np.arange(len(y))
            plt.plot(x, y, label=label, **kwargs)

        plt.legend()
        plt.title(title)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)

        if save:
            return self.save_plot(filename)
        return None

    # Bar plots
    def plot_bar(
        self,
        x: Union[np.ndarray, pd.Series, List[float]],
        y: Optional[Union[np.ndarray, pd.Series, List[float]]] = None,
        title: str = "Bar Plot",
        xlabel: str = "X",
        ylabel: str = "Y",
        color: Optional[str] = None,
        figsize: Tuple[int, int] = (10, 6),
        save: bool = False,
        filename: Optional[str] = None,
        **kwargs,
    ) -> Optional[str]:
        """
        Create a bar plot.

        Args:
            x: X-axis data or categories.
            y: Y-axis data (if None, use x as y and create index for x).
            title: Plot title.
            xlabel: X-axis label.
            ylabel: Y-axis label.
            color: Bar color.
            figsize: Figure size.
            save: Whether to save the plot.
            filename: Filename for saving.
            **kwargs: Additional arguments for plt.bar.

        Returns:
            Path to saved file if save=True, else None.
        """
        plt.figure(figsize=figsize)

        if y is None:
            y = x
            x = np.arange(len(y))

        plt.bar(x, y, color=color, **kwargs)

        plt.title(title)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)

        if save:
            return self.save_plot(filename)
        return None

    def plot_grouped_bar(
        self,
        data: Dict[str, Union[np.ndarray, pd.Series, List[float]]],
        categories: Optional[List[str]] = None,
        title: str = "Grouped Bar Plot",
        xlabel: str = "Categories",
        ylabel: str = "Values",
        figsize: Tuple[int, int] = (12, 6),
        save: bool = False,
        filename: Optional[str] = None,
        **kwargs,
    ) -> Optional[str]:
        """
        Create a grouped bar plot.

        Args:
            data: Dictionary of {group: values}.
            categories: Category labels.
            title: Plot title.
            xlabel: X-axis label.
            ylabel: Y-axis label.
            figsize: Figure size.
            save: Whether to save the plot.
            filename: Filename for saving.
            **kwargs: Additional arguments for plt.bar.

        Returns:
            Path to saved file if save=True, else None.
        """
        plt.figure(figsize=figsize)

        n_groups = len(data)
        n_categories = len(next(iter(data.values())))

        if categories is None:
            categories = [f"Category {i}" for i in range(n_categories)]

        bar_width = 0.8 / n_groups
        index = np.arange(n_categories)

        for i, (group, values) in enumerate(data.items()):
            plt.bar(
                index + i * bar_width,
                values,
                bar_width,
                label=group,
                **kwargs,
            )

        plt.title(title)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.xticks(index + bar_width * (n_groups - 1) / 2, categories)
        plt.legend()

        if save:
            return self.save_plot(filename)
        return None

    # Histograms and distributions
    def plot_histogram(
        self,
        data: Union[np.ndarray, pd.Series, List[float]],
        bins: int = 10,
        title: str = "Histogram",
        xlabel: str = "Value",
        ylabel: str = "Frequency",
        color: Optional[str] = None,
        density: bool = False,
        figsize: Tuple[int, int] = (10, 6),
        save: bool = False,
        filename: Optional[str] = None,
        **kwargs,
    ) -> Optional[str]:
        """
        Create a histogram.

        Args:
            data: Input data.
            bins: Number of bins.
            title: Plot title.
            xlabel: X-axis label.
            ylabel: Y-axis label.
            color: Color of the bars.
            density: If True, normalize to form a density.
            figsize: Figure size.
            save: Whether to save the plot.
            filename: Filename for saving.
            **kwargs: Additional arguments for plt.hist.

        Returns:
            Path to saved file if save=True, else None.
        """
        plt.figure(figsize=figsize)

        plt.hist(data, bins=bins, color=color, density=density, **kwargs)

        plt.title(title)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)

        if save:
            return self.save_plot(filename)
        return None

    def plot_distribution(
        self,
        data: Union[np.ndarray, pd.Series, List[float]],
        title: str = "Distribution Plot",
        xlabel: str = "Value",
        ylabel: str = "Density",
        color: Optional[str] = None,
        kde: bool = True,
        figsize: Tuple[int, int] = (10, 6),
        save: bool = False,
        filename: Optional[str] = None,
        **kwargs,
    ) -> Optional[str]:
        """
        Create a distribution plot using Seaborn.

        Args:
            data: Input data.
            title: Plot title.
            xlabel: X-axis label.
            ylabel: Y-axis label.
            color: Color of the distribution.
            kde: Whether to plot a kernel density estimate.
            figsize: Figure size.
            save: Whether to save the plot.
            filename: Filename for saving.
            **kwargs: Additional arguments for sns.histplot.

        Returns:
            Path to saved file if save=True, else None.
        """
        plt.figure(figsize=figsize)

        sns.histplot(data, kde=kde, color=color, **kwargs)

        plt.title(title)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)

        if save:
            return self.save_plot(filename)
        return None

    def plot_kde(
        self,
        data: Union[np.ndarray, pd.Series, List[float]],
        title: str = "Kernel Density Estimate",
        xlabel: str = "Value",
        ylabel: str = "Density",
        color: Optional[str] = None,
        figsize: Tuple[int, int] = (10, 6),
        save: bool = False,
        filename: Optional[str] = None,
        **kwargs,
    ) -> Optional[str]:
        """
        Create a kernel density estimate plot.

        Args:
            data: Input data.
            title: Plot title.
            xlabel: X-axis label.
            ylabel: Y-axis label.
            color: Color of the KDE.
            figsize: Figure size.
            save: Whether to save the plot.
            filename: Filename for saving.
            **kwargs: Additional arguments for sns.kdeplot.

        Returns:
            Path to saved file if save=True, else None.
        """
        plt.figure(figsize=figsize)

        sns.kdeplot(data, color=color, **kwargs)

        plt.title(title)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)

        if save:
            return self.save_plot(filename)
        return None

    # Scatter plots
    def plot_scatter(
        self,
        x: Union[np.ndarray, pd.Series, List[float]],
        y: Union[np.ndarray, pd.Series, List[float]],
        title: str = "Scatter Plot",
        xlabel: str = "X",
        ylabel: str = "Y",
        color: Optional[str] = None,
        alpha: float = 0.7,
        figsize: Tuple[int, int] = (10, 6),
        save: bool = False,
        filename: Optional[str] = None,
        **kwargs,
    ) -> Optional[str]:
        """
        Create a scatter plot.

        Args:
            x: X-axis data.
            y: Y-axis data.
            title: Plot title.
            xlabel: X-axis label.
            ylabel: Y-axis label.
            color: Color of the points.
            alpha: Transparency of the points.
            figsize: Figure size.
            save: Whether to save the plot.
            filename: Filename for saving.
            **kwargs: Additional arguments for plt.scatter.

        Returns:
            Path to saved file if save=True, else None.
        """
        plt.figure(figsize=figsize)

        plt.scatter(x, y, c=color, alpha=alpha, **kwargs)

        plt.title(title)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)

        if save:
            return self.save_plot(filename)
        return None

    def plot_scatter_with_regression(
        self,
        x: Union[np.ndarray, pd.Series, List[float]],
        y: Union[np.ndarray, pd.Series, List[float]],
        title: str = "Scatter Plot with Regression Line",
        xlabel: str = "X",
        ylabel: str = "Y",
        color: Optional[str] = None,
        figsize: Tuple[int, int] = (10, 6),
        save: bool = False,
        filename: Optional[str] = None,
        **kwargs,
    ) -> Optional[str]:
        """
        Create a scatter plot with a regression line.

        Args:
            x: X-axis data.
            y: Y-axis data.
            title: Plot title.
            xlabel: X-axis label.
            ylabel: Y-axis label.
            color: Color of the points.
            figsize: Figure size.
            save: Whether to save the plot.
            filename: Filename for saving.
            **kwargs: Additional arguments for sns.regplot.

        Returns:
            Path to saved file if save=True, else None.
        """
        plt.figure(figsize=figsize)

        sns.regplot(x=x, y=y, color=color, **kwargs)

        plt.title(title)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)

        if save:
            return self.save_plot(filename)
        return None

    # Box plots
    def plot_box(
        self,
        data: Union[np.ndarray, pd.DataFrame, List[List[float]]],
        labels: Optional[List[str]] = None,
        title: str = "Box Plot",
        xlabel: str = "Categories",
        ylabel: str = "Values",
        color: Optional[str] = None,
        figsize: Tuple[int, int] = (10, 6),
        save: bool = False,
        filename: Optional[str] = None,
        **kwargs,
    ) -> Optional[str]:
        """
        Create a box plot.

        Args:
            data: Input data (list of arrays or DataFrame).
            labels: Labels for each box.
            title: Plot title.
            xlabel: X-axis label.
            ylabel: Y-axis label.
            color: Color of the boxes.
            figsize: Figure size.
            save: Whether to save the plot.
            filename: Filename for saving.
            **kwargs: Additional arguments for plt.boxplot.

        Returns:
            Path to saved file if save=True, else None.
        """
        plt.figure(figsize=figsize)

        plt.boxplot(data, labels=labels, **kwargs)

        plt.title(title)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)

        if save:
            return self.save_plot(filename)
        return None

    def plot_boxplot(
        self,
        data: pd.DataFrame,
        x: str,
        y: str,
        hue: Optional[str] = None,
        title: str = "Box Plot",
        xlabel: str = None,
        ylabel: str = None,
        figsize: Tuple[int, int] = (10, 6),
        save: bool = False,
        filename: Optional[str] = None,
        **kwargs,
    ) -> Optional[str]:
        """
        Create a box plot using Seaborn.

        Args:
            data: Input DataFrame.
            x: Column name for x-axis.
            y: Column name for y-axis.
            hue: Column name for hue.
            title: Plot title.
            xlabel: X-axis label.
            ylabel: Y-axis label.
            figsize: Figure size.
            save: Whether to save the plot.
            filename: Filename for saving.
            **kwargs: Additional arguments for sns.boxplot.

        Returns:
            Path to saved file if save=True, else None.
        """
        plt.figure(figsize=figsize)

        sns.boxplot(data=data, x=x, y=y, hue=hue, **kwargs)

        plt.title(title)
        if xlabel:
            plt.xlabel(xlabel)
        if ylabel:
            plt.ylabel(ylabel)

        if save:
            return self.save_plot(filename)
        return None

    # Heatmaps
    def plot_heatmap(
        self,
        data: Union[np.ndarray, pd.DataFrame],
        title: str = "Heatmap",
        xlabel: str = "X",
        ylabel: str = "Y",
        annot: bool = True,
        fmt: str = ".2f",
        cmap: str = "viridis",
        figsize: Tuple[int, int] = (10, 8),
        save: bool = False,
        filename: Optional[str] = None,
        **kwargs,
    ) -> Optional[str]:
        """
        Create a heatmap.

        Args:
            data: Input data (2D array or DataFrame).
            title: Plot title.
            xlabel: X-axis label.
            ylabel: Y-axis label.
            annot: Whether to annotate cells with values.
            fmt: String formatting for annotations.
            cmap: Color map.
            figsize: Figure size.
            save: Whether to save the plot.
            filename: Filename for saving.
            **kwargs: Additional arguments for sns.heatmap.

        Returns:
            Path to saved file if save=True, else None.
        """
        plt.figure(figsize=figsize)

        sns.heatmap(data, annot=annot, fmt=fmt, cmap=cmap, **kwargs)

        plt.title(title)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)

        if save:
            return self.save_plot(filename)
        return None

    # Correlation matrix
    def plot_correlation_matrix(
        self,
        data: pd.DataFrame,
        title: str = "Correlation Matrix",
        annot: bool = True,
        fmt: str = ".2f",
        cmap: str = "coolwarm",
        figsize: Tuple[int, int] = (10, 8),
        save: bool = False,
        filename: Optional[str] = None,
        **kwargs,
    ) -> Optional[str]:
        """
        Plot a correlation matrix.

        Args:
            data: Input DataFrame.
            title: Plot title.
            annot: Whether to annotate cells with values.
            fmt: String formatting for annotations.
            cmap: Color map.
            figsize: Figure size.
            save: Whether to save the plot.
            filename: Filename for saving.
            **kwargs: Additional arguments for sns.heatmap.

        Returns:
            Path to saved file if save=True, else None.
        """
        plt.figure(figsize=figsize)

        corr_matrix = data.corr()
        sns.heatmap(corr_matrix, annot=annot, fmt=fmt, cmap=cmap, **kwargs)

        plt.title(title)

        if save:
            return self.save_plot(filename)
        return None

    # Pair plots
    def plot_pairplot(
        self,
        data: pd.DataFrame,
        hue: Optional[str] = None,
        title: str = "Pair Plot",
        figsize: Tuple[int, int] = (12, 12),
        save: bool = False,
        filename: Optional[str] = None,
        **kwargs,
    ) -> Optional[str]:
        """
        Create a pair plot (scatter plot matrix).

        Args:
            data: Input DataFrame.
            hue: Column name for color encoding.
            title: Plot title.
            figsize: Figure size.
            save: Whether to save the plot.
            filename: Filename for saving.
            **kwargs: Additional arguments for sns.pairplot.

        Returns:
            Path to saved file if save=True, else None.
        """
        g = sns.pairplot(data, hue=hue, **kwargs)
        g.fig.suptitle(title, y=1.02)

        if save:
            filepath = self.save_plot(filename)
            plt.close(g.fig)
            return filepath
        return None

    # Confusion matrix
    def plot_confusion_matrix(
        self,
        y_true: Union[np.ndarray, pd.Series, List[int]],
        y_pred: Union[np.ndarray, pd.Series, List[int]],
        classes: Optional[List[str]] = None,
        title: str = "Confusion Matrix",
        cmap: str = "Blues",
        figsize: Tuple[int, int] = (8, 6),
        save: bool = False,
        filename: Optional[str] = None,
        **kwargs,
    ) -> Optional[str]:
        """
        Plot a confusion matrix.

        Args:
            y_true: True labels.
            y_pred: Predicted labels.
            classes: Class names.
            title: Plot title.
            cmap: Color map.
            figsize: Figure size.
            save: Whether to save the plot.
            filename: Filename for saving.
            **kwargs: Additional arguments for sns.heatmap.

        Returns:
            Path to saved file if save=True, else None.
        """
        from sklearn.metrics import confusion_matrix

        cm = confusion_matrix(y_true, y_pred)

        plt.figure(figsize=figsize)

        sns.heatmap(cm, annot=True, fmt="d", cmap=cmap, xticklabels=classes, yticklabels=classes, **kwargs)

        plt.title(title)
        plt.xlabel("Predicted")
        plt.ylabel("True")

        if save:
            return self.save_plot(filename)
        return None

    # ROC curve
    def plot_roc_curve(
        self,
        y_true: Union[np.ndarray, pd.Series, List[int]],
        y_score: Union[np.ndarray, pd.Series, List[float]],
        title: str = "ROC Curve",
        label: str = "Model",
        color: Optional[str] = None,
        figsize: Tuple[int, int] = (8, 6),
        save: bool = False,
        filename: Optional[str] = None,
        **kwargs,
    ) -> Optional[str]:
        """
        Plot a ROC curve.

        Args:
            y_true: True labels.
            y_score: Predicted scores or probabilities.
            title: Plot title.
            label: Label for the ROC curve.
            color: Color of the ROC curve.
            figsize: Figure size.
            save: Whether to save the plot.
            filename: Filename for saving.
            **kwargs: Additional arguments for plt.plot.

        Returns:
            Path to saved file if save=True, else None.
        """
        from sklearn.metrics import roc_curve, auc

        fpr, tpr, _ = roc_curve(y_true, y_score)
        roc_auc = auc(fpr, tpr)

        plt.figure(figsize=figsize)

        plt.plot(fpr, tpr, color=color, label=f"{label} (AUC = {roc_auc:.2f})", **kwargs)
        plt.plot([0, 1], [0, 1], "k--", label="Random")

        plt.title(title)
        plt.xlabel("False Positive Rate")
        plt.ylabel("True Positive Rate")
        plt.legend(loc="lower right")

        if save:
            return self.save_plot(filename)
        return None

    # Training curves
    def plot_training_curves(
        self,
        history: Dict[str, List[float]],
        title: str = "Training Curves",
        figsize: Tuple[int, int] = (12, 6),
        save: bool = False,
        filename: Optional[str] = None,
        **kwargs,
    ) -> Optional[str]:
        """
        Plot training and validation curves.

        Args:
            history: Dictionary containing training history (loss, val_loss, etc.).
            title: Plot title.
            figsize: Figure size.
            save: Whether to save the plot.
            filename: Filename for saving.
            **kwargs: Additional arguments for plt.plot.

        Returns:
            Path to saved file if save=True, else None.
        """
        plt.figure(figsize=figsize)

        # Plot loss curves
        if "loss" in history:
            plt.plot(history["loss"], label="Training Loss", **kwargs)
        if "val_loss" in history:
            plt.plot(history["val_loss"], label="Validation Loss", **kwargs)

        plt.title(f"{title} - Loss")
        plt.xlabel("Epoch")
        plt.ylabel("Loss")
        plt.legend()

        if save:
            loss_file = self.save_plot(f"{filename}_loss" if filename else None)
        else:
            loss_file = None

        # Plot accuracy curves if available
        if "accuracy" in history or "val_accuracy" in history:
            plt.figure(figsize=figsize)

            if "accuracy" in history:
                plt.plot(history["accuracy"], label="Training Accuracy", **kwargs)
            if "val_accuracy" in history:
                plt.plot(history["val_accuracy"], label="Validation Accuracy", **kwargs)

            plt.title(f"{title} - Accuracy")
            plt.xlabel("Epoch")
            plt.ylabel("Accuracy")
            plt.legend()

            if save:
                acc_file = self.save_plot(f"{filename}_accuracy" if filename else None)
            else:
                acc_file = None

            return loss_file, acc_file

        return loss_file


# Global plotter instance
plotter = Plotter()
