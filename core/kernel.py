"""
Leon / Zenthon Kernel – sistemin əməliyyat mərkəzi.
"""

from __future__ import annotations

import os
import sys
import platform
from typing import Any, Dict, Optional

from core.config import config
from core.logger import logger
from core.event_bus import event_bus
from core.scheduler import scheduler
from core.service_registry import service_registry
from core.lifecycle import lifecycle, SystemState
from core.exceptions import KernelError


class SystemKernel:
    def __init__(self):
        self.config = config
        self._initialized = False

    def initialize(self) -> None:
        if self._initialized:
            return
        logger.info("Kernel: initialize()")
        lifecycle.initialize()
        self._check_environment()
        self._log_system_info()
        self._register_core_services()
        self._initialized = True
        logger.info("Kernel: initialized.")

    def start(self) -> None:
        if not self._initialized:
            self.initialize()
        logger.info("Kernel: start()")
        scheduler.start()
        lifecycle.start()

    def pause(self) -> None:
        lifecycle.pause()

    def resume(self) -> None:
        lifecycle.resume()

    def shutdown(self) -> None:
        logger.info("Kernel: shutdown()")
        scheduler.stop()
        lifecycle.shutdown()
        self._initialized = False

    def restart(self) -> None:
        self.shutdown()
        self.initialize()
        self.start()

    def _register_core_services(self) -> None:
        service_registry.register("event_bus", event_bus)
        service_registry.register("scheduler", scheduler)
        service_registry.register("lifecycle", lifecycle)
        service_registry.register("kernel", self)
        service_registry.register("config", config)
        service_registry.register("logger", logger)

        def _brain_factory():
            from brain import ThinkingBrain
            return ThinkingBrain(name="Leon")

        service_registry.register_factory("brain", _brain_factory)
        service_registry.register_factory(
            "llm",
            lambda: __import__("brain.llm", fromlist=["get_llm_client"]).get_llm_client(),
        )

    def _check_environment(self) -> None:
        required = ["numpy", "pandas"]
        optional = ["torch", "scikit-learn"]
        missing = []
        for pkg in required:
            try:
                __import__(pkg)
            except ImportError:
                missing.append(pkg)
        if missing:
            logger.warning(f"Missing required packages: {missing}")
        for pkg in optional:
            try:
                __import__(pkg)
            except ImportError:
                logger.debug(f"Optional package not found: {pkg}")

    def _log_system_info(self) -> None:
        info = {
            "System": platform.system(),
            "Machine": platform.machine(),
            "Python": sys.version.split()[0],
        }
        try:
            import psutil
            mem = psutil.virtual_memory()
            info["RAM_GB"] = f"{mem.total / (1024 ** 3):.1f}"
            info["CPU_cores"] = psutil.cpu_count()
        except Exception:
            pass
        try:
            import torch
            info["CUDA"] = str(torch.cuda.is_available())
        except Exception:
            info["CUDA"] = "n/a"
        logger.info("System info: " + ", ".join(f"{k}={v}" for k, v in info.items()))

    def get_system_resources(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {"state": lifecycle.get_state()}
        try:
            import psutil
            mem = psutil.virtual_memory()
            result["cpu_percent"] = psutil.cpu_percent(interval=0.3)
            result["memory"] = {
                "total": mem.total,
                "available": mem.available,
                "percent": mem.percent,
            }
        except Exception:
            pass
        return result

    def check_gpu_available(self) -> bool:
        try:
            import torch
            return torch.cuda.is_available()
        except Exception:
            return False

    def set_device(self, device: Optional[str] = None) -> str:
        if device is None:
            device = getattr(config.training, "device", "cpu")
        if device == "cuda" and not self.check_gpu_available():
            logger.warning("CUDA requested but not available. Falling back to CPU.")
            device = "cpu"
        return device

    def status(self) -> Dict[str, Any]:
        return {
            "state": lifecycle.get_state(),
            "initialized": self._initialized,
            "services": service_registry.list_services(),
            "tasks": scheduler.list_tasks(),
            "resources": self.get_system_resources(),
        }


kernel = SystemKernel()
