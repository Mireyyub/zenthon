"""Orchestrates communication between brain modules."""

from .core import Brain

class Orchestrator:
    def __init__(self, brain: Brain):
        self.brain = brain

    def run_cycle(self, input_data):
        return self.brain.think(input_data)
