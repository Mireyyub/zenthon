"""Path + execution sandbox (Faza 9)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, List, Optional, Sequence
import signal

from core.exceptions import SecurityError
from core.logger import logger


def _default_roots() -> List[Path]:
    try:
        from core.config import config

        leon = Path(config.path.leon_dir).resolve()
    except Exception:
        leon = Path("data/leon").resolve()
    sandbox = (leon / "sandbox").resolve()
    sandbox.mkdir(parents=True, exist_ok=True)
    return [sandbox, leon]


class PathSandbox:
    """Yalnız icazəli root altında path."""

    def __init__(self, roots: Optional[Sequence[Path | str]] = None):
        self.roots = [Path(r).resolve() for r in (roots or _default_roots())]

    def resolve(self, path: str, *, write: bool = False) -> Path:
        p = Path(path).expanduser()
        if not p.is_absolute():
            p = self.roots[0] / p
        p = p.resolve()
        ok = False
        for root in self.roots:
            try:
                p.relative_to(root)
                ok = True
                # write yalnız sandbox root (birinci)
                if write:
                    p.relative_to(self.roots[0])
                break
            except ValueError:
                continue
        if not ok:
            raise SecurityError(f"Path outside sandbox: {path}")
        return p


class Sandbox:
    """Timeout + path sandbox."""

    def __init__(self, timeout_seconds: int = 10):
        self.timeout = timeout_seconds
        self.paths = PathSandbox()

    def resolve_path(self, path: str, *, write: bool = False) -> Path:
        return self.paths.resolve(path, write=write)

    def run(self, func: Callable, *args, **kwargs) -> Any:
        def _handler(signum, frame):
            raise SecurityError(f"Sandbox timeout ({self.timeout}s)")

        try:
            old = signal.signal(signal.SIGALRM, _handler)
            signal.alarm(self.timeout)
            try:
                return func(*args, **kwargs)
            finally:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old)
        except AttributeError:
            logger.debug("Sandbox: SIGALRM not available")
            return func(*args, **kwargs)


sandbox = Sandbox()
