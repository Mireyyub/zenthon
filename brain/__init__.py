"""
Leon Brain – Multimodal Thinking Core.

    from brain import ThinkingBrain, BrainOrchestrator, reasoning_engine

    # Vahid yol (Faza 3):
    from brain.reasoning.engine import reasoning_engine
    r = reasoning_engine.reason("Daş mövcuddurmu?")
"""

from brain.core import Brain
from brain.orchestrator import Orchestrator, BrainOrchestrator
from brain.core_brain import ThinkingBrain
from brain.reasoning.engine import reasoning_engine, ReasoningEngine

__all__ = [
    "Brain",
    "Orchestrator",
    "BrainOrchestrator",
    "ThinkingBrain",
    "reasoning_engine",
    "ReasoningEngine",
]
__version__ = "0.5.0"
