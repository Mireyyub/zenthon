"""
Lifecycle manager – sistemin initialize / start / pause / resume / shutdown dövrü.
"""

from __future__ import annotations

from enum import Enum
from typing import Callable, List, Optional
import threading

from core.logger import logger
from core.event_bus import event_bus


class SystemState(str, Enum):
    CREATED = "created"
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    SHUTTING_DOWN = "shutting_down"
    STOPPED = "stopped"
    ERROR = "error"


class Lifecycle:
    def __init__(self):
        self.state = SystemState.CREATED
        self._lock = threading.RLock()
        self._on_start: List[Callable] = []
        self._on_shutdown: List[Callable] = []

    def on_start(self, callback: Callable) -> None:
        self._on_start.append(callback)

    def on_shutdown(self, callback: Callable) -> None:
        self._on_shutdown.append(callback)

    def initialize(self) -> None:
        with self._lock:
            self.state = SystemState.INITIALIZING
            logger.info("Lifecycle: initializing...")
            self.state = SystemState.READY
            event_bus.publish("SystemInitialized", source="lifecycle")

    def start(self) -> None:
        with self._lock:
            if self.state not in (SystemState.READY, SystemState.PAUSED, SystemState.STOPPED):
                logger.warning(f"Cannot start from state {self.state}")
                return
            for cb in self._on_start:
                try:
                    cb()
                except Exception as e:
                    logger.error(f"on_start callback error: {e}")
            self.state = SystemState.RUNNING
            event_bus.publish("SystemStarted", source="lifecycle")
            logger.info("Lifecycle: system RUNNING")

    def pause(self) -> None:
        with self._lock:
            if self.state != SystemState.RUNNING:
                return
            self.state = SystemState.PAUSED
            event_bus.publish("SystemPaused", source="lifecycle")
            logger.info("Lifecycle: system PAUSED")

    def resume(self) -> None:
        with self._lock:
            if self.state != SystemState.PAUSED:
                return
            self.state = SystemState.RUNNING
            event_bus.publish("SystemResumed", source="lifecycle")
            logger.info("Lifecycle: system RESUMED")

    def shutdown(self) -> None:
        with self._lock:
            self.state = SystemState.SHUTTING_DOWN
            logger.info("Lifecycle: shutting down...")
            for cb in reversed(self._on_shutdown):
                try:
                    cb()
                except Exception as e:
                    logger.error(f"on_shutdown callback error: {e}")
            self.state = SystemState.STOPPED
            event_bus.publish("SystemShutdown", source="lifecycle")
            logger.info("Lifecycle: system STOPPED")

    def get_state(self) -> str:
        return self.state.value


lifecycle = Lifecycle()
