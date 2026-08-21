from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from native_core.adapter import NativeCore


def test_native_core_uses_deterministic_python_fallback_without_binary():
    core = NativeCore(binary=None)

    normalized = core.normalize_text("  Zenthon\u00a0  AI  ")
    fingerprint = core.fingerprint("zenthon")
    metrics = core.token_metrics("Zenthon builds reliable AI")

    assert normalized.as_dict() == {
        "value": "Zenthon AI",
        "source": "python-fallback",
        "fallback_reason": "native binary unavailable",
    }
    assert fingerprint.source == "python-fallback"
    assert len(fingerprint.value) == 64
    assert metrics.value == {"characters": 26, "tokens": 4, "unique_tokens": 4, "lines": 1}


def test_native_core_uses_valid_json_from_explicit_binary(tmp_path: Path):
    binary = tmp_path / "native-core"
    binary.write_text("native binary placeholder", encoding="utf-8")
    with patch(
        "native_core.adapter.subprocess.run",
        return_value=SimpleNamespace(returncode=0, stdout='{"value":"native-result"}'),
    ):
        result = NativeCore(binary=binary).normalize_text("input")

    assert result.value == "native-result"
    assert result.source == "native-binary"
    assert result.fallback_reason is None


def test_native_core_rejects_unknown_operations_and_oversized_inputs():
    core = NativeCore()

    with pytest.raises(ValueError, match="Unsupported"):
        core.execute("shell", "no")
    with pytest.raises(ValueError, match="exceeds"):
        core.normalize_text("x" * (64 * 1024 + 1))
