"""Small, local-only settings store used before the full application config loads."""

from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
from typing import Any, Dict, Optional


_ALLOWED_KEYS = frozenset(
    {
        "data_dir",
        "event_persist",
        "first_run_complete",
        "model",
        "performance_mode",
        "profile_version",
        "voice_consent",
    }
)


def desktop_settings_path() -> Path:
    """Return the writable per-user configuration path, never the install folder."""
    override = os.getenv("LEON_SETTINGS_FILE")
    if override:
        return Path(override).expanduser()
    if os.name == "nt":
        root = Path(os.getenv("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
        return root / "Zenthon" / "settings.json"
    return Path.home() / ".local" / "share" / "zenthon" / "settings.json"


def load_desktop_settings(path: Optional[Path | str] = None) -> Dict[str, Any]:
    candidate = Path(path) if path else desktop_settings_path()
    try:
        loaded = json.loads(candidate.read_text(encoding="utf-8"))
        if isinstance(loaded, dict):
            return {key: loaded[key] for key in _ALLOWED_KEYS if key in loaded}
    except (OSError, json.JSONDecodeError, TypeError):
        pass
    return {}


def save_desktop_settings(values: Dict[str, Any], path: Optional[Path | str] = None) -> Dict[str, Any]:
    """Atomically store the allowlisted, non-secret desktop preferences."""
    candidate = Path(path) if path else desktop_settings_path()
    payload = {key: values[key] for key in _ALLOWED_KEYS if key in values}
    candidate.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".zenthon_", suffix=".json", dir=str(candidate.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, candidate)
    except Exception:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise
    return payload


def update_desktop_settings(values: Dict[str, Any], path: Optional[Path | str] = None) -> Dict[str, Any]:
    candidate = Path(path) if path else desktop_settings_path()
    merged = load_desktop_settings(candidate)
    merged.update(values)
    return save_desktop_settings(merged, candidate)
