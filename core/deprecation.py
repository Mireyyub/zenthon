"""
Consistent deprecation warnings for legacy entry points.

Phase 2 isolation: mark old paths without removing them.
"""

from __future__ import annotations

import warnings
from functools import wraps
from typing import Any, Callable, Optional, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


def warn_legacy(message: str, *,
                stacklevel: int = 2) -> None:
    """Emit a single DeprecationWarning with Leon context."""
    warnings.warn(
        f"[Leon LEGACY] {message}",
        DeprecationWarning,
        stacklevel=stacklevel,
    )


def deprecated(
    alternative: str,
    *,
    since: str = "0.7",
    remove_in: Optional[str] = None,
) -> Callable[[F], F]:
    """Decorator for functions/classes that should migrate to a canonical path."""

    def decorator(fn: F) -> F:
        msg = (
            f"{fn.__module__}.{fn.__qualname__} is deprecated since v{since}. "
            f"Use {alternative} instead."
        )
        if remove_in:
            msg += f" Planned removal: v{remove_in}."

        @wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            warn_legacy(msg, stacklevel=3)
            return fn(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator
