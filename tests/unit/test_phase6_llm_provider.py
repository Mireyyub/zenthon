"""Phase 6 — LLMProvider wired into reasoning path + RAG."""

from __future__ import annotations


def test_mock_provider_in_cot():
    from brain.llm.provider import MockProvider, set_llm_provider
    from brain.reasoning.chain_of_thought import ChainOfThought

    set_llm_provider(MockProvider(fixed_reply="1. Addım bir\n2. Addım iki\nNəticə: mock cavab"))
    try:
        r = ChainOfThought().reason("test sualı", context=["kontekst"])
        assert r["llm_used"] is True
        assert "mock" in str(r.get("conclusion", "")).lower() or "nəticə" in str(r.get("conclusion", "")).lower()
        assert r.get("llm_provider") == "mock"
        assert r["method"] == "chain_of_thought"
    finally:
        set_llm_provider(MockProvider())  # reset to safe mock for other tests


def test_mock_provider_in_tot():
    from brain.llm.provider import MockProvider, set_llm_provider
    from brain.reasoning.tree_of_thoughts import TreeOfThoughts

    set_llm_provider(
        MockProvider(
            fixed_reply="Budaq A\nBudaq B\nSeçilmiş: Analitik"
        )
    )
    try:
        r = TreeOfThoughts().reason("müqayisə et")
        assert r["llm_used"] is True
        assert r.get("llm_provider") == "mock"
        assert r["method"] == "tree_of_thoughts"
    finally:
        set_llm_provider(MockProvider())


def test_mock_provider_in_sot():
    from brain.llm.provider import MockProvider, set_llm_provider
    from brain.reasoning.skeleton_of_thought import SkeletonOfThought

    set_llm_provider(
        MockProvider(fixed_reply="1. Skelet\n2. Genişlənmə\nNəticə: struktur cavab")
    )
    try:
        r = SkeletonOfThought().reason("plan qur")
        assert r["llm_used"] is True
        assert r.get("llm_provider") == "mock"
        assert r["method"] == "skeleton_of_thought"
    finally:
        set_llm_provider(MockProvider())


def test_cot_fallback_when_provider_unavailable():
    from brain.llm.provider import MockProvider, set_llm_provider, LLMHealth
    from brain.reasoning.chain_of_thought import ChainOfThought

    class DownProvider(MockProvider):
        def health(self):
            return LLMHealth(provider="down", reachable=False, offline=True, error="offline")

        @property
        def is_available(self):
            return False

    set_llm_provider(DownProvider())
    try:
        r = ChainOfThought().reason("sadə sual")
        assert r["llm_used"] is False
        assert r["method"] == "chain_of_thought"
        assert "conclusion" in r
    finally:
        set_llm_provider(MockProvider())


def test_rag_generate_via_provider():
    from brain.llm.provider import MockProvider, set_llm_provider
    from brain.rag.pipeline import RAGPipeline

    set_llm_provider(MockProvider(fixed_reply="Kontekstə əsasən cavab: 42"))
    try:
        rag = RAGPipeline(persist_dir="/tmp/leon_rag_test_phase6")
        rag.ingest_text("Leon lokal AI sistemidir. Cavab 42-dir.", source="test")
        out = rag.query("Cavab nədir?", generate=True)
        assert out.get("answer")
        assert "42" in str(out["answer"])
        assert out.get("llm", {}).get("provider") == "mock"
    finally:
        set_llm_provider(MockProvider())


def test_get_llm_provider_default_and_mock():
    from brain.llm.provider import get_llm_provider, MockProvider, set_llm_provider

    p = get_llm_provider(prefer="mock")
    assert p.name == "mock"
    c = p.complete("x")
    assert c.ok

    set_llm_provider(MockProvider(fixed_reply="wired"))
    p2 = get_llm_provider()
    assert p2.complete("y").text == "wired"
    set_llm_provider(MockProvider())


def test_reasoning_engine_still_works_with_provider():
    """ReasoningEngine → ThinkingBrain → CoT must not crash."""
    from brain.llm.provider import MockProvider, set_llm_provider
    from brain.reasoning.engine import ReasoningEngine

    set_llm_provider(MockProvider(fixed_reply="1. Fakt\nNəticə: test OK"))
    try:
        eng = ReasoningEngine(persist_traces=False)
        # without strong curriculum/facts this may call brain
        out = eng.reason("Phase6 test", use_brain=True)
        assert "answer" in out or "conclusion" in out
        assert "confidence" in out
        assert "trace_id" in out
    finally:
        set_llm_provider(MockProvider())
