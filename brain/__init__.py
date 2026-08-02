"""
Zenthon Brain package – Multimodal Thinking Core.

    from brain import ThinkingBrain, BrainOrchestrator

    brain = ThinkingBrain()
    result = brain.think("Sual", reasoning_mode="auto")
    # async:
    result = await brain.athink("Sual")
"""

from brain.core import Brain
from brain.orchestrator import Orchestrator, BrainOrchestrator
from brain.core_brain import ThinkingBrain

__all__ = ["Brain", "Orchestrator", "BrainOrchestrator", "ThinkingBrain"]
__version__ = "0.4.0"
