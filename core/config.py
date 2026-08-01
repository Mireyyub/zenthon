"""
Configuration Module for AI System
Manages all system-wide configurations including model parameters, paths, and settings.
"""

import os
from dataclasses import dataclass, field
from typing import Dict, Any, Optional


@dataclass
class PathConfig:
    """Manages file and directory paths."""
    base_dir: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir: str = field(default_factory=lambda: os.path.join(PathConfig.base_dir, "data"))
    models_dir: str = field(default_factory=lambda: os.path.join(PathConfig.base_dir, "models"))
    logs_dir: str = field(default_factory=lambda: os.path.join(PathConfig.base_dir, "logs"))
    datasets_dir: str = field(default_factory=lambda: os.path.join(PathConfig.data_dir, "datasets"))
    saved_models_dir: str = field(default_factory=lambda: os.path.join(PathConfig.models_dir, "saved_models"))


@dataclass
class ModelConfig:
    """Configuration for machine learning and deep learning models."""
    input_size: int = 784
    hidden_size: int = 128
    output_size: int = 10
    learning_rate: float = 0.001
    batch_size: int = 32
    epochs: int = 10
    dropout: float = 0.2
    activation: str = "relu"


@dataclass
class TrainingConfig:
    """Configuration for training processes."""
    device: str = "cuda" if os.environ.get("CUDA_VISIBLE_DEVICES") else "cpu"
    mixed_precision: bool = True
    gradient_clip: Optional[float] = 1.0
    early_stopping_patience: int = 5


@dataclass
class SystemConfig:
    """Main system configuration."""
    path: PathConfig = field(default_factory=PathConfig)
    model: ModelConfig = field(default_factory=ModelConfig)
    training: TrainingConfig = field(default_factory=TrainingConfig)
    debug: bool = True
    log_level: str = "INFO"


# Global configuration instance
config = SystemConfig()


def load_config(config_file: Optional[str] = None) -> SystemConfig:
    """
    Load configuration from a YAML or JSON file.
    If no file is provided, returns the default configuration.
    """
    # TODO: Implement YAML/JSON config loading
    return config


def save_config(config: SystemConfig, config_file: str) -> None:
    """
    Save configuration to a YAML or JSON file.
    """
    # TODO: Implement YAML/JSON config saving
    pass
