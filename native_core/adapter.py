"""Safe bridge for optional Rust/C/C++ native helpers.

The Python implementation is always authoritative as a fallback. A native binary
is used only when it is explicitly available, returns a valid JSON envelope and
completes within the configured timeout.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


MAX_INPUT_BYTES = 64 * 1024
DEFAULT_TIMEOUT_SECONDS = 1.5
_TOKEN_PATTERN = re.compile(r"\b[\w'-]+\b", re.UNICODE)


class NativeCoreError(RuntimeError):
    """Raised for malformed optional native-core responses."""


@dataclass(frozen=True)
class CoreResult:
    value: Any
    source: str
    fallback_reason: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {"value": self.value, "source": self.source, "fallback_reason": self.fallback_reason}


def _normalize_text_python(text: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", text).split())


def _fingerprint_python(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _token_metrics_python(text: str) -> dict[str, int]:
    tokens = _TOKEN_PATTERN.findall(text)
    return {
        "characters": len(text),
        "tokens": len(tokens),
        "unique_tokens": len({token.casefold() for token in tokens}),
        "lines": 0 if not text else text.count("\n") + 1,
    }


class NativeCore:
    """Allowlist-only native helper client with reliable local fallbacks."""

    _fallbacks: dict[str, Callable[[str], Any]] = {
        "normalize_text": _normalize_text_python,
        "fingerprint": _fingerprint_python,
        "token_metrics": _token_metrics_python,
    }

    def __init__(self, binary: str | Path | None = None, timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS):
        configured = binary or os.getenv("ZENTHON_NATIVE_CORE_BIN")
        self.binary = Path(configured).expanduser() if configured else None
        self.timeout_seconds = timeout_seconds

    def available(self) -> bool:
        if not self.binary:
            return False
        return self.binary.is_file() or shutil.which(str(self.binary)) is not None

    def health(self) -> dict[str, Any]:
        return {
            "mode": "native-binary" if self.available() else "python-fallback",
            "binary": str(self.binary) if self.binary else None,
            "available": self.available(),
            "operations": sorted(self._fallbacks),
            "timeout_seconds": self.timeout_seconds,
        }

    def execute(self, operation: str, text: str) -> CoreResult:
        if operation not in self._fallbacks:
            raise ValueError(f"Unsupported native-core operation: {operation}")
        if not isinstance(text, str):
            raise TypeError("native-core text input must be a string")
        if len(text.encode("utf-8")) > MAX_INPUT_BYTES:
            raise ValueError(f"native-core input exceeds {MAX_INPUT_BYTES} bytes")

        if not self.available():
            return CoreResult(self._fallbacks[operation](text), "python-fallback", "native binary unavailable")

        try:
            completed = subprocess.run(
                [str(self.binary), operation],
                input=json.dumps({"text": text}, ensure_ascii=False),
                text=True,
                capture_output=True,
                timeout=self.timeout_seconds,
                check=False,
            )
            if completed.returncode != 0:
                raise NativeCoreError(f"native binary exited {completed.returncode}")
            payload = json.loads(completed.stdout)
            if not isinstance(payload, dict) or "value" not in payload:
                raise NativeCoreError("native binary returned an invalid envelope")
            return CoreResult(payload["value"], "native-binary")
        except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError, NativeCoreError) as exc:
            return CoreResult(self._fallbacks[operation](text), "python-fallback", str(exc))

    def normalize_text(self, text: str) -> CoreResult:
        return self.execute("normalize_text", text)

    def fingerprint(self, text: str) -> CoreResult:
        return self.execute("fingerprint", text)

    def token_metrics(self, text: str) -> CoreResult:
        return self.execute("token_metrics", text)


_core = NativeCore()


def get_native_core() -> NativeCore:
    return _core


def health_report() -> dict[str, Any]:
    return get_native_core().health()
