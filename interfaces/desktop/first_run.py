"""First-run profile service; GUI remains a thin client of these real settings."""

from __future__ import annotations

from dataclasses import dataclass
import os
import platform
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import urlparse

from core.desktop_settings import desktop_settings_path, load_desktop_settings, update_desktop_settings


@dataclass(frozen=True)
class HardwareProfile:
    os_name: str
    cpu_count: int
    memory_gb: Optional[float]
    cuda_available: bool
    gpu_names: tuple[str, ...]
    recommended_mode: str
    recommended_model: str

    @classmethod
    def detect(cls) -> "HardwareProfile":
        memory_gb: Optional[float] = None
        try:
            import psutil

            memory_gb = round(psutil.virtual_memory().total / (1024**3), 1)
        except Exception:
            pass

        cuda_available = False
        gpu_names: tuple[str, ...] = ()
        try:
            import torch

            cuda_available = bool(torch.cuda.is_available())
            if cuda_available:
                gpu_names = tuple(torch.cuda.get_device_name(index) for index in range(torch.cuda.device_count()))
        except Exception:
            pass

        if cuda_available and (memory_gb is None or memory_gb >= 12):
            mode, model = "performance", "llama3.2:3b"
        elif memory_gb is not None and memory_gb >= 8:
            mode, model = "balanced", "llama3.2:1b"
        else:
            mode, model = "low-resource", "llama3.2:1b"
        return cls(
            os_name=platform.system(),
            cpu_count=os.cpu_count() or 1,
            memory_gb=memory_gb,
            cuda_available=cuda_available,
            gpu_names=gpu_names,
            recommended_mode=mode,
            recommended_model=model,
        )

    def as_dict(self) -> Dict[str, Any]:
        return {
            "os_name": self.os_name,
            "cpu_count": self.cpu_count,
            "memory_gb": self.memory_gb,
            "cuda_available": self.cuda_available,
            "gpu_names": list(self.gpu_names),
            "recommended_mode": self.recommended_mode,
            "recommended_model": self.recommended_model,
        }


@dataclass(frozen=True)
class FirstRunProfile:
    data_dir: str
    model: str
    performance_mode: str
    voice_consent: bool
    event_persist: bool
    first_run_complete: bool = False
    profile_version: int = 1

    @classmethod
    def from_settings(cls, settings: Dict[str, Any], hardware: HardwareProfile) -> "FirstRunProfile":
        from core.config import config

        return cls(
            data_dir=str(settings.get("data_dir") or config.path.data_dir),
            model=str(settings.get("model") or config.llm.model or hardware.recommended_model),
            performance_mode=str(settings.get("performance_mode") or hardware.recommended_mode),
            voice_consent=bool(settings.get("voice_consent", False)),
            event_persist=bool(settings.get("event_persist", True)),
            first_run_complete=bool(settings.get("first_run_complete", False)),
            profile_version=int(settings.get("profile_version", 1)),
        )

    def as_dict(self) -> Dict[str, Any]:
        return {
            "data_dir": self.data_dir,
            "model": self.model,
            "performance_mode": self.performance_mode,
            "voice_consent": self.voice_consent,
            "event_persist": self.event_persist,
            "first_run_complete": self.first_run_complete,
            "profile_version": self.profile_version,
        }


class FirstRunService:
    """Persist first-run choices and update the active local configuration safely."""

    def __init__(self, settings_path: Optional[Path | str] = None):
        self.settings_path = Path(settings_path) if settings_path else desktop_settings_path()

    def hardware(self) -> HardwareProfile:
        return HardwareProfile.detect()

    def current_profile(self) -> FirstRunProfile:
        return FirstRunProfile.from_settings(load_desktop_settings(self.settings_path), self.hardware())

    def should_show(self) -> bool:
        return not self.current_profile().first_run_complete

    def apply(self, profile: FirstRunProfile) -> FirstRunProfile:
        data_dir = Path(profile.data_dir).expanduser().resolve()
        if str(data_dir) == data_dir.anchor:
            raise ValueError("Data directory cannot be a filesystem root")
        if profile.performance_mode not in {"low-resource", "balanced", "performance"}:
            raise ValueError("Unsupported performance mode")
        if not profile.model.strip():
            raise ValueError("A local model name is required")
        data_dir.mkdir(parents=True, exist_ok=True)
        completed = FirstRunProfile(
            data_dir=str(data_dir),
            model=profile.model.strip(),
            performance_mode=profile.performance_mode,
            voice_consent=bool(profile.voice_consent),
            event_persist=bool(profile.event_persist),
            first_run_complete=True,
            profile_version=1,
        )
        update_desktop_settings(completed.as_dict(), self.settings_path)
        if self.settings_path == desktop_settings_path():
            from core.config import apply_desktop_profile
            from core.event_bus import event_bus

            apply_desktop_profile(
                data_dir=data_dir,
                model=completed.model,
                event_persist=completed.event_persist,
            )
            event_bus.reconfigure_read_model()
        return completed


def model_health(timeout_seconds: float = 3.0) -> Dict[str, Any]:
    """Probe only a loopback Ollama model; never starts, pulls, or downloads it."""
    try:
        from brain.llm.client import get_llm_client

        client = get_llm_client(force_new=True)
        hostname = urlparse(client.config.base_url).hostname
        if client.config.provider != "ollama" or hostname not in {"127.0.0.1", "::1", "localhost"}:
            return {
                "provider": client.config.provider,
                "reachable": False,
                "status": "not-probed",
                "detail": "First-run setup probes loopback Ollama only.",
                "model": client.config.model,
            }
        client.config.timeout = min(max(float(timeout_seconds), 0.5), 5.0)
        return client.health_check()
    except Exception as error:
        return {"reachable": False, "error": f"{type(error).__name__}: {error}"}
