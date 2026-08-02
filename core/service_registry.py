"""
Service Registry – bütün sistem servislərinin qeydiyyat mərkəzi.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Type
import threading

from core.logger import logger
from core.exceptions import ServiceNotFoundError


class ServiceRegistry:
    """Singleton-style service container."""

    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Any] = {}
        self._lock = threading.RLock()

    def register(self, name: str, service: Any, replace: bool = False) -> None:
        with self._lock:
            if name in self._services and not replace:
                logger.warning(f"Service '{name}' already registered, skipping.")
                return
            self._services[name] = service
            logger.info(f"ServiceRegistry: registered '{name}'")

    def register_factory(self, name: str, factory: Any) -> None:
        """Lazy factory – get zamanı yaradılır."""
        with self._lock:
            self._factories[name] = factory

    def get(self, name: str) -> Any:
        with self._lock:
            if name in self._services:
                return self._services[name]
            if name in self._factories:
                service = self._factories[name]()
                self._services[name] = service
                del self._factories[name]
                return service
        raise ServiceNotFoundError(name)

    def has(self, name: str) -> bool:
        with self._lock:
            return name in self._services or name in self._factories

    def unregister(self, name: str) -> bool:
        with self._lock:
            if name in self._services:
                del self._services[name]
                return True
            if name in self._factories:
                del self._factories[name]
                return True
            return False

    def list_services(self) -> list:
        with self._lock:
            return sorted(list(self._services.keys()) + list(self._factories.keys()))

    def clear(self) -> None:
        with self._lock:
            self._services.clear()
            self._factories.clear()


service_registry = ServiceRegistry()
