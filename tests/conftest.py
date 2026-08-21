"""Shared pytest configuration for the lean, dependency-optional runtime."""

from __future__ import annotations

import importlib.util


# The core cognitive platform deliberately runs without the heavyweight PyTorch
# stack. Keep ML/DL suites available when PyTorch is installed, but do not make
# a local CLI/API smoke test fail in the default minimal environment.
collect_ignore: list[str] = []
if importlib.util.find_spec("torch") is None:
    collect_ignore.extend(
        [
            "integration/test_training_pipeline.py",
            "performance/test_model_performance.py",
            "unit/test_models.py",
        ]
    )
