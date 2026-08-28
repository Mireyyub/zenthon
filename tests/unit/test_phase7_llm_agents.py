"""Phase 7 — agents, vector embed, health via LLMProvider."""

from __future__ import annotations


def test_coding_agent_offline_template():
    from brain.llm.provider import MockProvider, set_llm_provider
    from agents.coding_agent import CodingAgent

    set_llm_provider(MockProvider(fixed_reply=""))  # empty → offline template

    class _Tools:
        def dispatch(self, name, argument):
            if name == "write_file":
                return {"ok": True}
            if name == "run_python":
                return {"ok": True, "stdout": "120"}
            return {}

    import tools.registry as reg

    old = getattr(reg, "tool_registry", None)
    reg.tool_registry = _Tools()
    try:
        r = CodingAgent().run("faktorial hesabla", {"run": True})
        assert r.success
        assert "factorial" in r.output["code"]
        assert r.metadata.get("llm_used") is False or r.metadata.get("provider")
    finally:
        if old is not None:
            reg.tool_registry = old


def test_react_offline_calc_heuristic():
    from brain.llm.provider import MockProvider, set_llm_provider
    from agents.react_agent import ReActAgent

    set_llm_provider(MockProvider(fixed_reply=""))

    class _Tools:
        def list_tools(self, production_only=True):
            return [{"name": "calc", "description": "calc"}]

        def dispatch(self, name, argument):
            if name == "calc":
                return eval(argument)  # noqa: S307 — test only, controlled expr
            raise AssertionError(name)

    import tools.registry as reg

    old = getattr(reg, "tool_registry", None)
    reg.tool_registry = _Tools()
    try:
        r = ReActAgent().run("2 + 2 hesabla", {"max_steps": 2})
        assert r.success
        assert r.output in (4, "4") or "4" in str(r.output)
    finally:
        if old is not None:
            reg.tool_registry = old


def test_research_agent_no_crash_offline():
    from brain.llm.provider import MockProvider, set_llm_provider
    from agents.research_agent import ResearchAgent

    set_llm_provider(MockProvider(fixed_reply="xülasə"))
    r = ResearchAgent().run("Daş nədir?")
    # May succeed with curriculum/retrieve or fail with no evidence — must not raise
    assert r is not None
    assert hasattr(r, "success")


def test_vector_memory_bow_without_dense():
    import tempfile
    from pathlib import Path
    from memory.vector_memory import VectorMemory
    from brain.llm.provider import MockProvider, set_llm_provider

    set_llm_provider(MockProvider())  # no embed → BOW only
    with tempfile.TemporaryDirectory() as td:
        vm = VectorMemory(path=Path(td) / "v.json", use_llm_embeddings=True)
        vm.add("Leon lokal AI sistemidir")
        hits = vm.search("Leon AI", top_k=2)
        assert len(hits) >= 1
        assert vm.backend() in ("bag_of_words", "auto", "hybrid_dense_bow")


def test_health_uses_provider():
    from interfaces.api.health import health_report

    report = health_report()
    assert "components" in report
    assert "llm" in report["components"]
    llm = report["components"]["llm"]
    assert "reachable" in llm or "error" in llm


def test_bootstrap_check_llm_dict():
    from core.bootstrap import _check_llm

    d = _check_llm()
    assert isinstance(d, dict)
    assert "reachable" in d or "error" in d
