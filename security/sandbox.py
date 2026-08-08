"""Path + execution sandbox (hardened)."""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence

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
                if write:
                    p.relative_to(self.roots[0])
                break
            except ValueError:
                continue
        if not ok:
            raise SecurityError(f"Path outside sandbox: {path}")
        return p


FORBIDDEN_SNIPPETS = (
    "os.system",
    "subprocess",
    "__import__",
    "eval(",
    "exec(",
    "open(",
    "socket",
    "ctypes",
    "pickle",
    "shutil.rmtree",
    "Path(",
)


class Sandbox:
    """Timeout + path sandbox + isolated python exec."""

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

    def check_code(self, code: str) -> None:
        low = code or ""
        for snip in FORBIDDEN_SNIPPETS:
            if snip in low:
                raise SecurityError(f"Forbidden snippet in sandbox code: {snip}")
        if len(low) > 8000:
            raise SecurityError("Code too long for sandbox")

    def run_python(
        self,
        code: str,
        *,
        timeout: Optional[int] = None,
        extra_env: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Run Python in a subprocess with cwd=sandbox root."""
        self.check_code(code)
        root = self.paths.roots[0]
        root.mkdir(parents=True, exist_ok=True)
        t = timeout if timeout is not None else self.timeout
        env = os.environ.copy()
        env["PYTHONPATH"] = ""
        env["LEON_SANDBOX"] = "1"
        if extra_env:
            env.update(extra_env)
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", dir=str(root), delete=False, encoding="utf-8"
        ) as f:
            f.write(code)
            script = f.name
        try:
            proc = subprocess.run(
                [sys.executable, script],
                cwd=str(root),
                capture_output=True,
                text=True,
                timeout=t,
                env=env,
            )
            return {
                "ok": proc.returncode == 0,
                "returncode": proc.returncode,
                "stdout": (proc.stdout or "")[:4000],
                "stderr": (proc.stderr or "")[:2000],
            }
        except subprocess.TimeoutExpired:
            raise SecurityError(f"Sandbox python timeout ({t}s)")
        finally:
            try:
                Path(script).unlink(missing_ok=True)
            except Exception:
                pass


sandbox = Sandbox()
