"""
Kernel Module for AI System
Manages system resources, dependencies, and core operations.
"""

import os
import sys
import platform
import psutil
import GPUtil
from typing import Dict, Any, Optional

from core.config import config
from core.logger import logger


class SystemKernel:
    """Manages system resources and environment for AI operations."""

    def __init__(self):
        self.config = config
        self._check_environment()
        self._log_system_info()

    def _check_environment(self) -> None:
        """Check if required dependencies are available."""
        required_packages = [
            "numpy",
            "torch",
            "pandas",
            "scikit-learn",
        ]

        missing_packages = []
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                missing_packages.append(package)

        if missing_packages:
            logger.warning(
                f"Missing required packages: {', '.join(missing_packages)}. "
                "Install them with: pip install " + " ".join(missing_packages)
            )

    def _log_system_info(self) -> None:
        """Log system information for debugging."""
        info = {
            "System": platform.system(),
            "Node Name": platform.node(),
            "Release": platform.release(),
            "Version": platform.version(),
            "Machine": platform.machine(),
            "Processor": platform.processor(),
            "Python Version": sys.version,
        }

        # Memory info
        mem = psutil.virtual_memory()
        info["Total Memory (GB)"] = f"{mem.total / (1024 ** 3):.2f}"
        info["Available Memory (GB)"] = f"{mem.available / (1024 ** 3):.2f}"

        # GPU info
        try:
            gpus = GPUtil.getGPUs()
            gpu_info = [f"{gpu.id}: {gpu.name} ({gpu.memoryTotal}MB)" for gpu in gpus]
            info["GPUs"] = ", ".join(gpu_info) if gpu_info else "None"
        except Exception:
            info["GPUs"] = "Not available"

        logger.info("System Information:")
        for key, value in info.items():
            logger.info(f"  {key}: {value}")

    def get_system_resources(self) -> Dict[str, Any]:
        """Get current system resource usage."""
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)

        # Memory usage
        mem = psutil.virtual_memory()
        mem_usage = {
            "total": mem.total,
            "available": mem.available,
            "used": mem.used,
            "percent": mem.percent,
        }

        # GPU usage
        gpu_usage = {}
        try:
            gpus = GPUtil.getGPUs()
            for gpu in gpus:
                gpu_usage[f"gpu_{gpu.id}"] = {
                    "name": gpu.name,
                    "memory_total": gpu.memoryTotal,
                    "memory_used": gpu.memoryUsed,
                    "memory_free": gpu.memoryFree,
                    "utilization": gpu.load * 100,
                }
        except Exception:
            pass

        return {
            "cpu_percent": cpu_percent,
            "memory": mem_usage,
            "gpu": gpu_usage,
        }

    def check_gpu_available(self) -> bool:
        """Check if GPU is available for acceleration."""
        try:
            import torch
            return torch.cuda.is_available()
        except Exception:
            return False

    def set_device(self, device: Optional[str] = None) -> str:
        """Set the device for computation (CPU or GPU)."""
        if device is None:
            device = config.training.device

        if device == "cuda" and not self.check_gpu_available():
            logger.warning("CUDA requested but not available. Falling back to CPU.")
            device = "cpu"

        return device


# Global kernel instance
kernel = SystemKernel()
