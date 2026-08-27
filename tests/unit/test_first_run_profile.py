from __future__ import annotations

from pathlib import Path

import pytest


def test_first_run_service_persists_profile_and_marks_completion(tmp_path: Path):
    from interfaces.desktop.first_run import FirstRunProfile, FirstRunService

    settings = tmp_path / "settings.json"
    service = FirstRunService(settings)
    assert service.should_show() is True

    completed = service.apply(
        FirstRunProfile(
            data_dir=str(tmp_path / "ZenthonData"),
            model="llama3.2:1b",
            performance_mode="low-resource",
            voice_consent=False,
            event_persist=True,
        )
    )

    assert completed.first_run_complete is True
    assert Path(completed.data_dir).is_dir()
    assert service.should_show() is False
    assert service.current_profile().model == "llama3.2:1b"


def test_desktop_settings_configure_next_process_data_and_model(monkeypatch, tmp_path: Path):
    from core.desktop_settings import save_desktop_settings

    settings = tmp_path / "settings.json"
    selected_data = tmp_path / "selected-data"
    save_desktop_settings(
        {"data_dir": str(selected_data), "model": "llama3.2:3b", "event_persist": False},
        settings,
    )
    monkeypatch.setenv("LEON_SETTINGS_FILE", str(settings))

    import core.config as config_module

    cfg = config_module.load_config()
    assert cfg.path.data_dir == selected_data
    assert cfg.llm.model == "llama3.2:3b"
    assert cfg.events.persist is False


def test_first_run_service_rejects_filesystem_root_as_data_dir(tmp_path: Path):
    from interfaces.desktop.first_run import FirstRunProfile, FirstRunService

    profile = FirstRunProfile(
        data_dir=Path(tmp_path).anchor,
        model="llama3.2:1b",
        performance_mode="low-resource",
        voice_consent=False,
        event_persist=True,
    )
    with pytest.raises(ValueError, match="filesystem root"):
        FirstRunService(tmp_path / "settings.json").apply(profile)


def test_first_run_profile_has_safe_hardware_recommendation():
    from interfaces.desktop.first_run import HardwareProfile

    profile = HardwareProfile.detect()
    assert profile.cpu_count >= 1
    assert profile.recommended_mode in {"low-resource", "balanced", "performance"}
    assert profile.recommended_model


def test_model_health_never_probes_nonlocal_provider(monkeypatch):
    from brain.llm.client import LLMConfig
    from interfaces.desktop.first_run import model_health

    class Client:
        config = LLMConfig(provider="openai", base_url="https://api.example.test/v1", model="remote")

        def health_check(self):
            raise AssertionError("nonlocal model health must not be probed during first-run setup")

    monkeypatch.setattr("brain.llm.client.get_llm_client", lambda force_new=True: Client())
    report = model_health()
    assert report["status"] == "not-probed"
    assert report["reachable"] is False
