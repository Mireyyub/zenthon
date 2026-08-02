"""
Zenthon Brain package – Multimodal Thinking Core.

Əsas istifadə:
    from brain import ThinkingBrain

    brain = ThinkingBrain()
    result = brain.think("Sualınız", goal="Məqsəd", reasoning_mode="auto")
"""

from brain.core import Brain
from brain.orchestrator import Orchestrator
from brain.core_brain import ThinkingBrain

__all__ = ["Brain", "Orchestrator", "ThinkingBrain"]
__version__ = "0.2.0"
