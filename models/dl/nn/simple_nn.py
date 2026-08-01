"""
Simple Neural Network Model
Basic feedforward neural network implementation using PyTorch.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, List, Callable

from core.logger import logger
from core.config import config


class SimpleNN(nn.Module):
    """
    Simple Feedforward Neural Network.
    
    A basic neural network with configurable number of layers and units.
    """

    def __init__(
        self,
        input_size: int,
        hidden_sizes: List[int],
        output_size: int,
        activation: str = "relu",
        dropout: float = 0.0,
    ):
        """
        Initialize SimpleNN.

        Args:
            input_size: Size of input features.
            hidden_sizes: List of hidden layer sizes.
            output_size: Size of output layer.
            activation: Activation function ('relu', 'sigmoid', 'tanh').
            dropout: Dropout rate.
        """
        super(SimpleNN, self).__init__()
        self.input_size = input_size
        self.hidden_sizes = hidden_sizes
        self.output_size = output_size
        self.activation = activation
        self.dropout = dropout

        # Create layers
        self.layers = nn.ModuleList()

        # Input layer
        prev_size = input_size
        for i, size in enumerate(hidden_sizes):
            self.layers.append(nn.Linear(prev_size, size))
            prev_size = size

        # Output layer
        self.output_layer = nn.Linear(prev_size, output_size)

        # Dropout layer
        self.dropout_layer = nn.Dropout(dropout)

        # Initialize weights
        self._initialize_weights()

        logger.info(
            f"SimpleNN initialized: input={input_size}, "
            f"hidden={hidden_sizes}, output={output_size}, "
            f"activation={activation}, dropout={dropout}"
        )

    def _initialize_weights(self) -> None:
        """Initialize weights using Xavier/Glorot initialization."""
        for layer in self.layers:
            nn.init.xavier_uniform_(layer.weight)
            nn.init.zeros_(layer.bias)
        nn.init.xavier_uniform_(self.output_layer.weight)
        nn.init.zeros_(self.output_layer.bias)

    def _get_activation(self) -> Callable:
        """Get the activation function."""
        if self.activation == "relu":
            return F.relu
        elif self.activation == "sigmoid":
            return torch.sigmoid
        elif self.activation == "tanh":
            return torch.tanh
        else:
            raise ValueError(f"Unknown activation: {self.activation}")

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass of the network.

        Args:
            x: Input tensor (batch_size, input_size).

        Returns:
            Output tensor (batch_size, output_size).
        """
        activate = self._get_activation()

        # Hidden layers
        for layer in self.layers:
            x = layer(x)
            x = activate(x)
            x = self.dropout_layer(x)

        # Output layer
        x = self.output_layer(x)

        return x


class MLP(nn.Module):
    """
    Multi-Layer Perceptron.
    
    A more flexible neural network with customizable architecture.
    """

    def __init__(
        self,
        layer_sizes: List[int],
        activation: str = "relu",
        dropout: float = 0.0,
        use_batch_norm: bool = False,
    ):
        """
        Initialize MLP.

        Args:
            layer_sizes: List of layer sizes including input and output.
            activation: Activation function ('relu', 'sigmoid', 'tanh', 'leaky_relu').
            dropout: Dropout rate.
            use_batch_norm: Whether to use batch normalization.
        """
        super(MLP, self).__init__()
        self.layer_sizes = layer_sizes
        self.activation = activation
        self.dropout = dropout
        self.use_batch_norm = use_batch_norm

        # Create layers
        self.layers = nn.ModuleList()
        for i in range(len(layer_sizes) - 1):
            self.layers.append(nn.Linear(layer_sizes[i], layer_sizes[i + 1]))

        # Batch norm layers
        self.bn_layers = nn.ModuleList()
        if use_batch_norm:
            for i in range(len(layer_sizes) - 1):
                if i < len(layer_sizes) - 2:  # No batch norm on output layer
                    self.bn_layers.append(nn.BatchNorm1d(layer_sizes[i + 1]))

        # Dropout layer
        self.dropout_layer = nn.Dropout(dropout)

        # Initialize weights
        self._initialize_weights()

        logger.info(
            f"MLP initialized: layers={layer_sizes}, "
            f"activation={activation}, dropout={dropout}, "
            f"batch_norm={use_batch_norm}"
        )

    def _initialize_weights(self) -> None:
        """Initialize weights using He initialization for ReLU, Xavier for others."""
        for layer in self.layers:
            if self.activation == "relu":
                nn.init.kaiming_uniform_(layer.weight, mode='fan_in', nonlinearity='relu')
            else:
                nn.init.xavier_uniform_(layer.weight)
            nn.init.zeros_(layer.bias)

    def _get_activation(self) -> Callable:
        """Get the activation function."""
        if self.activation == "relu":
            return F.relu
        elif self.activation == "sigmoid":
            return torch.sigmoid
        elif self.activation == "tanh":
            return torch.tanh
        elif self.activation == "leaky_relu":
            return F.leaky_relu
        else:
            raise ValueError(f"Unknown activation: {self.activation}")

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass of the network.

        Args:
            x: Input tensor (batch_size, input_size).

        Returns:
            Output tensor (batch_size, output_size).
        """
        activate = self._get_activation()

        for i, layer in enumerate(self.layers):
            x = layer(x)

            # Apply batch norm if available and not last layer
            if self.use_batch_norm and i < len(self.layers) - 1:
                x = self.bn_layers[i](x)

            # Apply activation if not last layer
            if i < len(self.layers) - 1:
                x = activate(x)
                x = self.dropout_layer(x)

        return x


class SimpleNNFactory:
    """Factory for creating SimpleNN models with default configurations."""

    @staticmethod
    def create_classifier(
        input_size: int,
        num_classes: int,
        hidden_sizes: Optional[List[int]] = None,
    ) -> SimpleNN:
        """
        Create a classifier neural network.

        Args:
            input_size: Input feature size.
            num_classes: Number of output classes.
            hidden_sizes: List of hidden layer sizes.

        Returns:
            SimpleNN model for classification.
        """
        if hidden_sizes is None:
            hidden_sizes = [128, 64]

        return SimpleNN(
            input_size=input_size,
            hidden_sizes=hidden_sizes,
            output_size=num_classes,
            activation="relu",
            dropout=0.2,
        )

    @staticmethod
    def create_regressor(
        input_size: int,
        output_size: int = 1,
        hidden_sizes: Optional[List[int]] = None,
    ) -> SimpleNN:
        """
        Create a regressor neural network.

        Args:
            input_size: Input feature size.
            output_size: Output size (default 1 for single output).
            hidden_sizes: List of hidden layer sizes.

        Returns:
            SimpleNN model for regression.
        """
        if hidden_sizes is None:
            hidden_sizes = [128, 64]

        return SimpleNN(
            input_size=input_size,
            hidden_sizes=hidden_sizes,
            output_size=output_size,
            activation="relu",
            dropout=0.0,
        )
