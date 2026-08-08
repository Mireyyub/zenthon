"""
Leon Brain – cognitive core exports.

Canonical think path:

    from brain import reasoning_engine, BrainOrchestrator
    r = reasoning_engine.reason("Daş mövcuddurmu?")
    # or
    orch = BrainOrchestrator()
    r = orch.run("Daş mövcuddurmu?")

ThinkingBrain is an internal LLM backend (not the public think API).
"""

from brain.orchestrator import BrainOrchestrator
from brain.reasoning.engine import reasoning_engine, ReasoningEngine

# Back-compat import (prefer ReasoningEngine / Orchestrator)
from brain.core_brain import ThinkingBrain  # noqa: F401
from brain.core import Brain  # noqa: F401 — legacy stub
from brain.orchestrator import Orchestrator  # noqa: F401

__all__ = [
    "BrainOrchestrator",
    "reasoning_engine",
    "ReasoningEngine",
    "ThinkingBrain",
    "Brain",
    "Orchestrator",
]
__version__ = "0.6.0"
