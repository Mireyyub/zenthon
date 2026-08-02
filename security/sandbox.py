"""Sandbox – təhlükəsiz kod icrası üçün məhdudiyyətlər."""

from __future__ import annotations

from typing import Any, Callable, Optional
import signal

from core.exceptions import SecurityError
from core.logger import logger


class Sandbox:
    """Sadə timeout əsaslı sandbox."""

    def __init__(self, timeout_seconds: int = 10):
        self.timeout = timeout_seconds

    def run(self, func: Callable, *args, **kwargs) -> Any:
        """Funksiyanı timeout ilə icra et (Unix)."""
        def _handler(signum, frame):
            raise SecurityError(f"Sandbox timeout ({self.timeout}s)")

        try:
            old = signal.signal(signal.SIGALRM, _handler)
            signal.alarm(self.timeout)
            try:
                result = func(*args, **kwargs)
            finally:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old)
            return result
        except AttributeError:
            # Windows-da SIGALRM yoxdur – birbaşa icra
            logger.debug("Sandbox: SIGALRM not available, running without timeout")
            return func(*args, **kwargs)
