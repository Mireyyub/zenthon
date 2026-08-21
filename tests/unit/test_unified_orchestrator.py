from agents.unified_orchestrator import UnifiedAgentOrchestrator


class _Result:
    def __init__(self, output): self.success, self.output, self.error = True, output, None


class _Manager:
    def __init__(self): self.calls = []
    def create(self, name, **_): return type("Agent", (), {"id": name})()
    def run(self, agent_id, task, context):
        self.calls.append((agent_id, task, dict(context)))
        return _Result(f"{agent_id}:{task}")


def test_unified_orchestrator_passes_outputs_between_agents():
    manager = _Manager()
    result = UnifiedAgentOrchestrator(manager).run("plan", ["react", "coding"])
    assert result["ok"] is True
    assert manager.calls[1][2]["react"] == "react:plan"
