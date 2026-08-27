from __future__ import annotations


def test_llm_environment_values_are_bounded_or_fall_back(monkeypatch):
    import core.config as config_module

    monkeypatch.setenv("LEON_LLM_TIMEOUT", "invalid")
    monkeypatch.setenv("LEON_LLM_TEMPERATURE", "99")
    monkeypatch.setenv("LEON_LLM_MAX_TOKENS", "-10")
    monkeypatch.setenv("LEON_DEBUG", "off")

    cfg = config_module.load_config()
    assert cfg.llm.timeout == 120.0
    assert cfg.llm.temperature == 2.0
    assert cfg.llm.max_tokens == 1
    assert cfg.debug is False
