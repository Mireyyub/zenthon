"""
Leon / Zenthon – vahid konfiqurasiya.

Env:
  LEON_DATA_DIR, LEON_LLM_PROVIDER, LEON_LLM_MODEL, LEON_EMBED_MODEL,
  LEON_OLLAMA_HOST, LEON_LOG_LEVEL, ZENTHON_* (legacy aliases)
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _env(key: str, default: str = "", *aliases: str) -> str:
    for k in (key,) + aliases:
        v = os.getenv(k)
        if v is not None and str(v).strip() != "":
            return str(v).strip()
    return default


@dataclass
class PathConfig:
    """Disk yolları – bütün persist data `leon_dir` altındadır."""

    base_dir: Path = field(default_factory=_repo_root)
    data_dir: Path = field(default_factory=lambda: _repo_root() / "data")
    leon_dir: Path = field(default_factory=lambda: _repo_root() / "data" / "leon")
    facts_dir: Path = field(default_factory=lambda: _repo_root() / "data" / "leon" / "facts")
    graph_dir: Path = field(default_factory=lambda: _repo_root() / "data" / "leon" / "graph")
    memory_dir: Path = field(default_factory=lambda: _repo_root() / "data" / "leon" / "memory")
    learning_dir: Path = field(default_factory=lambda: _repo_root() / "data" / "leon" / "learning")
    traces_dir: Path = field(default_factory=lambda: _repo_root() / "data" / "leon" / "traces")
    checkpoints_dir: Path = field(default_factory=lambda: _repo_root() / "data" / "leon" / "checkpoints")
    logs_dir: Path = field(default_factory=lambda: _repo_root() / "logs")
    models_dir: Path = field(default_factory=lambda: _repo_root() / "models")
    datasets_dir: Path = field(default_factory=lambda: _repo_root() / "data" / "datasets")
    saved_models_dir: Path = field(default_factory=lambda: _repo_root() / "models" / "saved_models")

    def ensure(self) -> "PathConfig":
        for p in (
            self.data_dir,
            self.leon_dir,
            self.facts_dir,
            self.graph_dir,
            self.memory_dir,
            self.learning_dir,
            self.traces_dir,
            self.checkpoints_dir,
            self.logs_dir,
            self.datasets_dir,
            self.saved_models_dir,
        ):
            Path(p).mkdir(parents=True, exist_ok=True)
        return self

    def as_dict(self) -> Dict[str, str]:
        return {
            "base_dir": str(self.base_dir),
            "data_dir": str(self.data_dir),
            "leon_dir": str(self.leon_dir),
            "facts_dir": str(self.facts_dir),
            "graph_dir": str(self.graph_dir),
            "memory_dir": str(self.memory_dir),
            "learning_dir": str(self.learning_dir),
            "traces_dir": str(self.traces_dir),
            "checkpoints_dir": str(self.checkpoints_dir),
            "logs_dir": str(self.logs_dir),
        }


@dataclass
class LLMSettings:
    provider: str = "ollama"
    base_url: str = "http://localhost:11434/v1"
    ollama_host: str = "http://localhost:11434"
    api_key: str = "ollama"
    model: str = "llama3.2"
    embed_model: str = "nomic-embed-text"
    timeout: float = 120.0
    temperature: float = 0.4
    max_tokens: int = 1024

    def as_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider,
            "base_url": self.base_url,
            "ollama_host": self.ollama_host,
            "model": self.model,
            "embed_model": self.embed_model,
            "timeout": self.timeout,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "api_key_set": bool(self.api_key),
        }


@dataclass
class ModelConfig:
    input_size: int = 784
    hidden_size: int = 128
    output_size: int = 10
    learning_rate: float = 0.001
    batch_size: int = 32
    epochs: int = 10
    dropout: float = 0.2
    activation: str = "relu"


@dataclass
class TrainingConfig:
    device: str = field(
        default_factory=lambda: "cuda" if os.environ.get("CUDA_VISIBLE_DEVICES") else "cpu"
    )
    mixed_precision: bool = True
    gradient_clip: Optional[float] = 1.0
    early_stopping_patience: int = 5


@dataclass
class SystemConfig:
    path: PathConfig = field(default_factory=PathConfig)
    llm: LLMSettings = field(default_factory=LLMSettings)
    model: ModelConfig = field(default_factory=ModelConfig)
    training: TrainingConfig = field(default_factory=TrainingConfig)
    debug: bool = True
    log_level: str = "INFO"
    ai_name: str = "Leon"

    def ensure_dirs(self) -> "SystemConfig":
        self.path.ensure()
        return self

    def load_config(self, config_file: Optional[str] = None) -> "SystemConfig":
        """Legacy instance API retained for integrations that reload settings."""
        return load_config(config_file)


def _build_paths() -> PathConfig:
    root = _repo_root()
    data_override = _env("LEON_DATA_DIR", "", "ZENTHON_DATA_DIR")
    data_dir = Path(data_override) if data_override else root / "data"
    leon_dir = data_dir / "leon"
    return PathConfig(
        base_dir=root,
        data_dir=data_dir,
        leon_dir=leon_dir,
        facts_dir=leon_dir / "facts",
        graph_dir=leon_dir / "graph",
        memory_dir=leon_dir / "memory",
        learning_dir=leon_dir / "learning",
        traces_dir=leon_dir / "traces",
        checkpoints_dir=leon_dir / "checkpoints",
        logs_dir=root / "logs",
        models_dir=root / "models",
        datasets_dir=data_dir / "datasets",
        saved_models_dir=root / "models" / "saved_models",
    )


def _build_llm() -> LLMSettings:
    provider = _env("LEON_LLM_PROVIDER", "ollama", "ZENTHON_LLM_PROVIDER", "LLM_PROVIDER").lower()
    ollama_host = _env("LEON_OLLAMA_HOST", "http://localhost:11434", "OLLAMA_HOST").rstrip("/")
    presets = {
        "ollama": {
            "base_url": f"{ollama_host}/v1",
            "api_key": "ollama",
            "model": "llama3.2",
        },
        "openai": {
            "base_url": "https://api.openai.com/v1",
            "api_key": "",
            "model": "gpt-4o-mini",
        },
        "xai": {
            "base_url": "https://api.x.ai/v1",
            "api_key": "",
            "model": "grok-3",
        },
        "groq": {
            "base_url": "https://api.groq.com/openai/v1",
            "api_key": "",
            "model": "llama-3.3-70b-versatile",
        },
    }
    preset = presets.get(provider, presets["ollama"])
    api_key = _env(
        "LEON_LLM_API_KEY",
        preset.get("api_key", ""),
        "ZENTHON_LLM_API_KEY",
        "OPENAI_API_KEY",
        "XAI_API_KEY",
        "GROQ_API_KEY",
    )
    if provider == "ollama" and not api_key:
        api_key = "ollama"
    base_url = _env("LEON_LLM_BASE_URL", preset["base_url"], "ZENTHON_LLM_BASE_URL")
    model = _env("LEON_LLM_MODEL", preset["model"], "ZENTHON_LLM_MODEL")
    embed_model = _env("LEON_EMBED_MODEL", "nomic-embed-text", "ZENTHON_EMBED_MODEL")
    return LLMSettings(
        provider=provider,
        base_url=base_url,
        ollama_host=ollama_host if provider == "ollama" else base_url,
        api_key=api_key,
        model=model,
        embed_model=embed_model,
        timeout=float(_env("LEON_LLM_TIMEOUT", "120", "ZENTHON_LLM_TIMEOUT")),
        temperature=float(_env("LEON_LLM_TEMPERATURE", "0.4", "ZENTHON_LLM_TEMPERATURE")),
        max_tokens=int(_env("LEON_LLM_MAX_TOKENS", "1024", "ZENTHON_LLM_MAX_TOKENS")),
    )


def load_config(config_file: Optional[str] = None) -> SystemConfig:
    """Env-dən SystemConfig qur. config_file hələ optional (Faza 1)."""
    cfg = SystemConfig(
        path=_build_paths(),
        llm=_build_llm(),
        model=ModelConfig(),
        training=TrainingConfig(),
        debug=_env("LEON_DEBUG", "1", "ZENTHON_DEBUG") not in ("0", "false", "False"),
        log_level=_env("LEON_LOG_LEVEL", "INFO", "ZENTHON_LOG_LEVEL").upper(),
        ai_name=_env("LEON_AI_NAME", "Leon"),
    )
    cfg.ensure_dirs()
    return cfg


def save_config(cfg: SystemConfig, config_file: str) -> None:
    """Minimal JSON dump (opsional)."""
    import json

    payload = {
        "ai_name": cfg.ai_name,
        "log_level": cfg.log_level,
        "debug": cfg.debug,
        "paths": cfg.path.as_dict(),
        "llm": cfg.llm.as_dict(),
    }
    Path(config_file).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


# Global – process start-da env oxunur
config: SystemConfig = load_config()
