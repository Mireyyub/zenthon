from agents.coding_agent import CodingAgent


class _EmptyProvider:
    name = "mock"
    is_available = True

    def complete(self, *_args, **_kwargs):
        from brain.llm.provider import LLMCompletion

        return LLMCompletion(text="", model="mock", provider="mock", error="empty")


class _Tools:
    def dispatch(self, name, argument):
        if name == "write_file":
            return {"written": len(argument)}
        if name == "run_python":
            return {"ok": True}
        raise AssertionError(name)


def test_coding_agent_uses_offline_code_when_llm_reply_is_empty(monkeypatch):
    import brain.llm.provider as provider_module
    import tools.registry as registry_module

    monkeypatch.setattr(provider_module, "get_llm_provider", lambda **_: _EmptyProvider())
    monkeypatch.setattr(registry_module, "tool_registry", _Tools())
    result = CodingAgent().run("faktorial hesabla", {"run": True})
    assert result.success is True
    assert "def factorial" in result.output["code"]
