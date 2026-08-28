"""
Leon Brain – cognitive core exports.

Canonical think path:

    from brain import reasoning_engine, BrainOrchestrator
    r = reasoning_engine.reason("Daş mövcuddurmu?")

Self layers (advanced): brain.self_view, brain.self_improve,
brain.self_mutate, brain.system_loop — import explicitly.

INTERNAL (not for app code):
    ThinkingBrain  — LLM backend inside ReasoningEngine only
    Brain          — thin legacy stub
"""

from brain.orchestrator import BrainOrchestrator
from brain.reasoning.engine import reasoning_engine, ReasoningEngine

# Back-compat (internal / legacy — prefer BrainOrchestrator + ReasoningEngine)
from brain.core_brain import ThinkingBrain  # noqa: F401
from brain.core import Brain  # noqa: F401
from brain.orchestrator import Orchestrator  # noqa: F401

# Bind broader mutate allowlist into SelfMutateEngine
try:
    from brain.policy_bind import bind_mutate_policy

    bind_mutate_policy()
except Exception:
    pass

__all__ = [
    "BrainOrchestrator",
    "reasoning_engine",
    "ReasoningEngine",
    # legacy exports kept for import compat
    "ThinkingBrain",
    "Brain",
    "Orchestrator",
]
__version__ = "0.7.0"
