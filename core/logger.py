"""
Logger Module for AI System
Provides logging utilities for tracking system operations, errors, and metrics.
"""

import logging
import os
import sys
from datetime import datetime
from typing import Optional

from core.config import config


class AILogger:
    """Custom logger for AI System with file and console output."""

    def __init__(
        self,
        name: str = "AI_System",
        log_dir: Optional[str] = None,
        log_file: Optional[str] = None,
        level: str = None,
    ):
        self.name = name
        self.log_dir = log_dir or config.path.logs_dir
        self.log_file = log_file or f"{self.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        self.level = level or config.log_level

        # Create log directory if it doesn't exist
        os.makedirs(self.log_dir, exist_ok=True)

        # Set up logger
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(getattr(logging, self.level.upper()))

        # Prevent duplicate handlers
        if self.logger.handlers:
            return

        # Create formatter
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s] - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # File handler
        file_path = os.path.join(self.log_dir, self.log_file)
        file_handler = logging.FileHandler(file_path)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

    def debug(self, message: str) -> None:
        """Log debug message."""
        self.logger.debug(message)

    def info(self, message: str) -> None:
        """Log info message."""
        self.logger.info(message)

    def warning(self, message: str) -> None:
        """Log warning message."""
        self.logger.warning(message)

    def error(self, message: str) -> None:
        """Log error message."""
        self.logger.error(message)

    def critical(self, message: str) -> None:
        """Log critical message."""
        self.logger.critical(message)

    def log_metrics(self, metrics: dict, prefix: str = "Metrics") -> None:
        """Log training or evaluation metrics."""
        metrics_str = ", ".join(f"{k}: {v:.4f}" for k, v in metrics.items())
        self.info(f"{prefix} - {metrics_str}")


# Global logger instance
logger = AILogger()


def get_logger(name: str) -> AILogger:
    """Get a logger instance with the specified name."""
    return AILogger(name=name)
