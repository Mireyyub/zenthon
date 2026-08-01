"""
Simple CNN Model
Convolutional Neural Network implementation for image classification.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, List, Tuple

from core.logger import logger


class SimpleCNN(nn.Module):
    """
    Simple Convolutional Neural Network for image classification.
    
    Architecture:
    - Conv2d -> ReLU -> MaxPool2d
    - Conv2d -> ReLU -> MaxPool2d
    - Flatten -> Linear -> ReLU -> Dropout
    - Linear (output)
    """

    def __init__(
        self,
        in_channels: int = 3,
        num_classes: int = 10,
        conv_layers: Optional[List[Tuple[int, int, int]]] = None,
        fc_sizes: Optional[List[int]] = None,
        dropout: float = 0.5,
    ):
        """
        Initialize SimpleCNN.

        Args:
            in_channels: Number of input channels (1 for grayscale, 3 for RGB).
            num_classes: Number of output classes.
            conv_layers: List of tuples (out_channels, kernel_size, stride).
            fc_sizes: List of fully connected layer sizes.
            dropout: Dropout rate.
        """
        super(SimpleCNN, self).__init__()
        self.in_channels = in_channels
        self.num_classes = num_classes
        self.dropout = dropout

        # Default conv layers if not provided
        if conv_layers is None:
            conv_layers = [
                (32, 3, 1),  # (out_channels, kernel_size, stride)
                (64, 3, 1),
            ]

        # Default fc layers if not provided
        if fc_sizes is None:
            fc_sizes = [128]

        # Build convolutional layers
        self.conv_layers = nn.ModuleList()
        prev_channels = in_channels

        for i, (out_channels, kernel_size, stride) in enumerate(conv_layers):
            conv = nn.Conv2d(
                in_channels=prev_channels,
                out_channels=out_channels,
                kernel_size=kernel_size,
                stride=stride,
                padding=kernel_size // 2,  # Same padding
            )
            self.conv_layers.append(conv)
            prev_channels = out_channels

        # Pooling layer
        self.pool = nn.MaxPool2d(kernel_size=2, stride=2)

        # Build fully connected layers
        self.fc_layers = nn.ModuleList()
        prev_size = prev_channels

        for size in fc_sizes:
            self.fc_layers.append(nn.Linear(prev_size, size))
            prev_size = size

        # Output layer
        self.output_layer = nn.Linear(prev_size, num_classes)

        # Dropout layer
        self.dropout_layer = nn.Dropout(dropout)

        # Initialize weights
        self._initialize_weights()

        logger.info(
            f"SimpleCNN initialized: in_channels={in_channels}, "
            f"num_classes={num_classes}, conv_layers={conv_layers}, "
            f"fc_sizes={fc_sizes}, dropout={dropout}"
        )

    def _initialize_weights(self) -> None:
        """Initialize weights using He initialization."""
        for layer in self.conv_layers:
            nn.init.kaiming_uniform_(layer.weight, mode='fan_in', nonlinearity='relu')
            if layer.bias is not None:
                nn.init.constant_(layer.bias, 0)

        for layer in self.fc_layers:
            nn.init.kaiming_uniform_(layer.weight, mode='fan_in', nonlinearity='relu')
            nn.init.constant_(layer.bias, 0)

        nn.init.xavier_uniform_(self.output_layer.weight)
        nn.init.constant_(self.output_layer.bias, 0)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass of the network.

        Args:
            x: Input tensor (batch_size, in_channels, height, width).

        Returns:
            Output tensor (batch_size, num_classes).
        """
        # Convolutional layers
        for conv in self.conv_layers:
            x = conv(x)
            x = F.relu(x)
            x = self.pool(x)

        # Flatten
        x = torch.flatten(x, 1)

        # Fully connected layers
        for fc in self.fc_layers:
            x = fc(x)
            x = F.relu(x)
            x = self.dropout_layer(x)

        # Output layer
        x = self.output_layer(x)

        return x


class CNNFactory:
    """Factory for creating CNN models with common architectures."""

    @staticmethod
    def create_mnist_classifier(in_channels: int = 1, num_classes: int = 10) -> SimpleCNN:
        """
        Create a CNN for MNIST classification.

        Args:
            in_channels: Input channels (1 for MNIST).
            num_classes: Number of classes (10 for MNIST).

        Returns:
            SimpleCNN model for MNIST.
        """
        return SimpleCNN(
            in_channels=in_channels,
            num_classes=num_classes,
            conv_layers=[
                (32, 3, 1),
                (64, 3, 1),
            ],
            fc_sizes=[128],
            dropout=0.5,
        )

    @staticmethod
    def create_cifar_classifier(in_channels: int = 3, num_classes: int = 10) -> SimpleCNN:
        """
        Create a CNN for CIFAR-10 classification.

        Args:
            in_channels: Input channels (3 for CIFAR-10).
            num_classes: Number of classes (10 for CIFAR-10).

        Returns:
            SimpleCNN model for CIFAR-10.
        """
        return SimpleCNN(
            in_channels=in_channels,
            num_classes=num_classes,
            conv_layers=[
                (32, 3, 1),
                (64, 3, 1),
                (128, 3, 1),
            ],
            fc_sizes=[256, 128],
            dropout=0.5,
        )

    @staticmethod
    def create_small_cnn(in_channels: int = 3, num_classes: int = 10) -> SimpleCNN:
        """
        Create a small CNN for quick testing.

        Args:
            in_channels: Input channels.
            num_classes: Number of classes.

        Returns:
            SimpleCNN model with minimal architecture.
        """
        return SimpleCNN(
            in_channels=in_channels,
            num_classes=num_classes,
            conv_layers=[
                (16, 3, 1),
            ],
            fc_sizes=[32],
            dropout=0.2,
        )
