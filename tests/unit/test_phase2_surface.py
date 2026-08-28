"""Phase 2 — public surface isolation checks (no behavior change)."""

from __future__ import annotations


def test_public_imports_smoke():
    from core import config, logger, event_bus
    from brain import BrainOrchestrator, reasoning_engine, ReasoningEngine
    from knowledge import get_fact_store, get_graph
    from memory import MemoryManager, retrieve
    from curriculum import CurriculumEngine
    from agents import agent_manager, BaseAgent, AgentResult
    from security import safe_tool_call, tool_allowlist
    from tools import tool_registry
    from core.contracts import Task, EventName, AgentMessage
    from brain.llm import get_llm_provider, MockProvider

    assert config is not None
    assert logger is not None
    assert event_bus is not None
    assert BrainOrchestrator is not None
    assert reasoning_engine is not None
    assert ReasoningEngine is not None
    assert callable(get_fact_store)
    assert callable(get_graph)
    assert MemoryManager is not None
    assert callable(retrieve)
    assert CurriculumEngine is not None
    assert agent_manager is not None
    assert BaseAgent is not None
    assert AgentResult is not None
    assert callable(safe_tool_call)
    assert tool_allowlist is not None
    assert tool_registry is not None
    assert Task is not None
    assert EventName is not None
    assert AgentMessage is not None
    assert get_llm_provider is not None
    assert MockProvider is not None


def test_api_default_bind_is_localhost():
    from interfaces.api import main as api_main

    assert api_main._default_host() == "127.0.0.1" or isinstance(api_main._default_host(), str)
    # Without env override, must be loopback
    import os

    os.environ.pop("LEON_API_HOST", None)
    os.environ.pop("ZENTHON_API_HOST", None)
    assert api_main._default_host() == "127.0.0.1"
    assert api_main._default_port() == 8000


def test_api_version_aligned():
    from interfaces.api.main import app

    assert app.version.startswith("0.7")


def test_deprecation_helper():
    import warnings
    from core.deprecation import warn_legacy, deprecated

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        warn_legacy("test message")
        assert any(issubclass(x.category, DeprecationWarning) for x in w)

    @deprecated("new_fn", since="0.7")
    def old_fn():
        return 42

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        assert old_fn() == 42
        assert any("deprecated" in str(x.message).lower() for x in w)


def test_brain_version():
    import brain

    assert brain.__version__ == "0.7.0"
