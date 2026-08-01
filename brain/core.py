"""Core brain module for Zenthon."""

class Brain:
    def __init__(self):
        self.modules = {}
        self.state = "idle"

    def register_module(self, name, module):
        self.modules[name] = module

    def think(self, input_data):
        return {
            "status": "initialized",
            "input": input_data,
            "modules": list(self.modules.keys())
        }
