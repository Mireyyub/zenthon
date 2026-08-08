"""
Leon Brain – cognitive core exports.

Canonical think path:

    from brain import reasoning_engine, BrainOrchestrator
    r = reasoning_engine.reason("Daş mövcuddurmu?")

Self layers: self_view, self_improve, self_mutate, self_code, system_loop
"""

from brain.orchestrator import BrainOrchestrator
from brain.reasoning.engine import reasoning_engine, ReasoningEngine

# Back-compat
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
    "ThinkingBrain",
    "Brain",
    "Orchestrator",
]
__version__ = "0.7.0"
