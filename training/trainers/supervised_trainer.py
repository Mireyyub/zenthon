"""
Supervised Trainer Module
Provides training utilities for supervised learning models.
"""

import os
import time
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from typing import Optional, Dict, Any, List, Callable, Union
from sklearn.base import BaseEstimator
from sklearn.metrics import accuracy_score, mean_squared_error

from core.logger import logger
from core.config import config
from core.kernel import kernel


class SupervisedTrainer:
    """
    Trainer for supervised learning models.
    
    Supports both scikit-learn style models and PyTorch models.
    """

    def __init__(
        self,
        model: Union[BaseEstimator, nn.Module],
        optimizer: Optional[optim.Optimizer] = None,
        criterion: Optional[nn.Module] = None,
        device: Optional[str] = None,
        metrics: Optional[List[str]] = None,
    ):
        """
        Initialize SupervisedTrainer.

        Args:
            model: Model to train (scikit-learn or PyTorch).
            optimizer: Optimizer for PyTorch models.
            criterion: Loss function for PyTorch models.
            device: Device to use ('cpu' or 'cuda').
            metrics: List of metrics to track.
        """
        self.model = model
        self.optimizer = optimizer
        self.criterion = criterion
        self.device = device or kernel.set_device()
        self.metrics = metrics or ["accuracy"]
        self.history = {
            "loss": [],
            "val_loss": [],
        }
        for metric in self.metrics:
            self.history[f"{metric}"] = []
            self.history[f"val_{metric}"] = []

        # Determine model type
        self.is_pytorch = isinstance(model, nn.Module)

        if self.is_pytorch:
            self.model.to(self.device)
            if optimizer is None:
                self.optimizer = optim.Adam(model.parameters(), lr=config.model.learning_rate)
            if criterion is None:
                # Default to CrossEntropyLoss for classification, MSE for regression
                if hasattr(model, "output_size") and model.output_size > 1:
                    self.criterion = nn.CrossEntropyLoss()
                else:
                    self.criterion = nn.MSELoss()

        logger.info(
            f"SupervisedTrainer initialized: model_type={'PyTorch' if self.is_pytorch else 'Scikit-learn'}, "
            f"device={self.device}, metrics={self.metrics}"
        )

    def train(
        self,
        X_train: Union[np.ndarray, torch.Tensor],
        y_train: Union[np.ndarray, torch.Tensor],
        X_val: Optional[Union[np.ndarray, torch.Tensor]] = None,
        y_val: Optional[Union[np.ndarray, torch.Tensor]] = None,
        epochs: int = 10,
        batch_size: int = 32,
        validation_split: float = 0.0,
        callbacks: Optional[List[Callable]] = None,
    ) -> Dict[str, List[float]]:
        """
        Train the model.

        Args:
            X_train: Training features.
            y_train: Training targets.
            X_val: Validation features.
            y_val: Validation targets.
            epochs: Number of training epochs.
            batch_size: Batch size for training.
            validation_split: Fraction of training data to use for validation.
            callbacks: List of callback functions to call during training.

        Returns:
            Training history.
        """
        if callbacks is None:
            callbacks = []

        # Convert numpy arrays to tensors if using PyTorch
        if self.is_pytorch:
            X_train = self._to_tensor(X_train)
            y_train = self._to_tensor(y_train)

            if X_val is not None and y_val is not None:
                X_val = self._to_tensor(X_val)
                y_val = self._to_tensor(y_val)
            elif validation_split > 0:
                # Split training data for validation
                split_idx = int(len(X_train) * (1 - validation_split))
                X_val, y_val = X_train[split_idx:], y_train[split_idx:]
                X_train, y_train = X_train[:split_idx], y_train[:split_idx]

            # Create DataLoader
            train_dataset = TensorDataset(X_train, y_train)
            train_loader = DataLoader(
                train_dataset,
                batch_size=batch_size,
                shuffle=True,
            )

            if X_val is not None:
                val_dataset = TensorDataset(X_val, y_val)
                val_loader = DataLoader(
                    val_dataset,
                    batch_size=batch_size,
                    shuffle=False,
                )
            else:
                val_loader = None

            # Training loop
            for epoch in range(epochs):
                # Train
                train_loss = self._train_epoch(train_loader)
                self.history["loss"].append(train_loss)

                # Evaluate
                if val_loader is not None:
                    val_loss, val_metrics = self._evaluate(val_loader)
                    self.history["val_loss"].append(val_loss)

                    for metric_name, metric_value in val_metrics.items():
                        self.history[f"val_{metric_name}"].append(metric_value)

                # Evaluate on training data
                train_metrics = self._evaluate(train_loader, training=True)
                for metric_name, metric_value in train_metrics.items():
                    self.history[metric_name].append(metric_value)

                # Call callbacks
                for callback in callbacks:
                    callback(
                        epoch=epoch,
                        loss=train_loss,
                        val_loss=val_loss if val_loader is not None else None,
                        metrics=train_metrics,
                        val_metrics=val_metrics if val_loader is not None else None,
                    )

                # Log progress
                log_str = f"Epoch {epoch + 1}/{epochs} - loss: {train_loss:.4f}"
                if val_loader is not None:
                    log_str += f" - val_loss: {val_loss:.4f}"
                for metric_name, metric_value in train_metrics.items():
                    log_str += f" - {metric_name}: {metric_value:.4f}"
                if val_loader is not None:
                    for metric_name, metric_value in val_metrics.items():
                        log_str += f" - val_{metric_name}: {metric_value:.4f}"
                logger.info(log_str)

        else:
            # Scikit-learn style training
            self.model.fit(X_train, y_train)

            # Evaluate
            if X_val is not None and y_val is not None:
                for metric in self.metrics:
                    if metric == "accuracy":
                        score = accuracy_score(y_val, self.model.predict(X_val))
                    elif metric == "mse":
                        score = mean_squared_error(y_val, self.model.predict(X_val))
                    else:
                        score = 0.0
                    self.history[metric].append(score)

        return self.history

    def _train_epoch(self, data_loader: DataLoader) -> float:
        """Train for one epoch."""
        self.model.train()
        total_loss = 0.0
        num_batches = 0

        for X_batch, y_batch in data_loader:
            X_batch, y_batch = X_batch.to(self.device), y_batch.to(self.device)

            # Forward pass
            self.optimizer.zero_grad()
            outputs = self.model(X_batch)

            # Compute loss
            loss = self.criterion(outputs, y_batch)

            # Backward pass
            loss.backward()
            self.optimizer.step()

            total_loss += loss.item()
            num_batches += 1

        return total_loss / num_batches

    def _evaluate(
        self,
        data_loader: DataLoader,
        training: bool = False,
    ) -> Dict[str, float]:
        """Evaluate the model on a dataset."""
        self.model.eval()
        total_loss = 0.0
        num_batches = 0

        # Collect predictions and targets for metrics
        all_preds = []
        all_targets = []

        with torch.no_grad():
            for X_batch, y_batch in data_loader:
                X_batch, y_batch = X_batch.to(self.device), y_batch.to(self.device)

                # Forward pass
                outputs = self.model(X_batch)

                # Compute loss
                loss = self.criterion(outputs, y_batch)
                total_loss += loss.item()
                num_batches += 1

                # Store predictions and targets
                if hasattr(self.model, "output_size") and self.model.output_size > 1:
                    # Classification
                    preds = torch.argmax(outputs, dim=1)
                else:
                    # Regression
                    preds = outputs

                all_preds.append(preds.cpu().numpy())
                all_targets.append(y_batch.cpu().numpy())

        # Calculate metrics
        metrics = {}
        avg_loss = total_loss / num_batches

        # Flatten predictions and targets
        all_preds = np.concatenate(all_preds)
        all_targets = np.concatenate(all_targets)

        for metric in self.metrics:
            if metric == "accuracy":
                metrics[metric] = accuracy_score(all_targets, all_preds)
            elif metric == "mse":
                metrics[metric] = mean_squared_error(all_targets, all_preds)
            elif metric == "mae":
                metrics[metric] = np.mean(np.abs(all_targets - all_preds))

        return {**{"loss": avg_loss}, **metrics}

    def _to_tensor(self, data: Union[np.ndarray, torch.Tensor]) -> torch.Tensor:
        """Convert data to tensor if it's a numpy array."""
        if isinstance(data, np.ndarray):
            return torch.from_numpy(data).float()
        return data

    def predict(self, X: Union[np.ndarray, torch.Tensor]) -> np.ndarray:
        """
        Make predictions using the trained model.

        Args:
            X: Input data.

        Returns:
            Predictions.
        """
        if self.is_pytorch:
            self.model.eval()
            X = self._to_tensor(X).to(self.device)
            with torch.no_grad():
                outputs = self.model(X)
                if hasattr(self.model, "output_size") and self.model.output_size > 1:
                    # Classification: return class indices
                    preds = torch.argmax(outputs, dim=1)
                else:
                    # Regression: return raw outputs
                    preds = outputs
            return preds.cpu().numpy()
        else:
            return self.model.predict(X)

    def evaluate(
        self,
        X: Union[np.ndarray, torch.Tensor],
        y: Union[np.ndarray, torch.Tensor],
    ) -> Dict[str, float]:
        """
        Evaluate the model on a test set.

        Args:
            X: Test features.
            y: Test targets.

        Returns:
            Dictionary of metrics.
        """
        if self.is_pytorch:
            X = self._to_tensor(X)
            y = self._to_tensor(y)
            test_dataset = TensorDataset(X, y)
            test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False)
            return self._evaluate(test_loader)
        else:
            metrics = {}
            preds = self.model.predict(X)
            for metric in self.metrics:
                if metric == "accuracy":
                    metrics[metric] = accuracy_score(y, preds)
                elif metric == "mse":
                    metrics[metric] = mean_squared_error(y, preds)
            return metrics

    def save_model(self, filepath: Optional[str] = None) -> None:
        """
        Save the trained model.

        Args:
            filepath: Path to save the model. If None, uses default path.
        """
        if filepath is None:
            filepath = os.path.join(
                config.path.saved_models_dir,
                f"model_{time.strftime('%Y%m%d_%H%M%S')}.pt"
            )

        if self.is_pytorch:
            torch.save(self.model.state_dict(), filepath)
        else:
            import joblib
            joblib.dump(self.model, filepath)

        logger.info(f"Model saved to {filepath}")

    def load_model(self, filepath: str) -> None:
        """
        Load a trained model.

        Args:
            filepath: Path to the saved model.
        """
        if self.is_pytorch:
            self.model.load_state_dict(torch.load(filepath, map_location=self.device))
            self.model.to(self.device)
        else:
            import joblib
            self.model = joblib.load(filepath)

        logger.info(f"Model loaded from {filepath}")
