"""
Desktop readiness probe (Phase 8).

Honest status for hybrid local desktop target.
Does NOT claim Tauri/React shell until those exist.
Rust native_core is optional accelerator only — never AI logic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class DesktopReadiness:
    """Single snapshot for desktop packaging / UI shell decisions."""

    target: str = "hybrid-local-desktop"
    platform_priority: str = "windows-11-first"
    cognitive_core: str = "python"
    api_ready: bool = False
    llm_reachable: bool = False
    llm_soft: bool = True
    native_mode: str = "python-fallback"
    native_available: bool = False
    security_gate: bool = False
    storage_sqlite: bool = False
    ui_today: str = "tkinter-legacy"
    ui_target: str = "react-tauri"
    shell_today: str = "python-scripts"
    shell_target: str = "tauri-rust-supervisor"
    offline_capable: bool = True
    blockers: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target": self.target,
            "platform_priority": self.platform_priority,
            "cognitive_core": self.cognitive_core,
            "api_ready": self.api_ready,
            "llm_reachable": self.llm_reachable,
            "llm_soft": self.llm_soft,
            "native_mode": self.native_mode,
            "native_available": self.native_available,
            "security_gate": self.security_gate,
            "storage_sqlite": self.storage_sqlite,
            "ui_today": self.ui_today,
            "ui_target": self.ui_target,
            "shell_today": self.shell_today,
            "shell_target": self.shell_target,
            "offline_capable": self.offline_capable,
            "blockers": list(self.blockers),
            "notes": list(self.notes),
            "ready_for_tauri": self.ready_for_tauri,
            "ready_for_production_desktop": False,  # honest: not yet
        }

    @property
    def ready_for_tauri(self) -> bool:
        """API + security + storage enough to attach a thin shell."""
        return self.api_ready and self.security_gate and not any(
            b.startswith("critical:") for b in self.blockers
        )


def desktop_readiness() -> DesktopReadiness:
    r = DesktopReadiness()
    r.notes.append(
        "Cognitive Python core is production-grade within prototype scope."
    )
    r.notes.append(
        "Tauri + React UI not shipped; Tkinter remains the local GUI."
    )

    # API surface
    try:
        from interfaces.api.main import app

        r.api_ready = app is not None
    except Exception as e:
        r.api_ready = False
        r.blockers.append(f"critical: FastAPI app import failed: {e}")

    # LLM (soft)
    try:
        from brain.llm.provider import get_llm_provider

        h = get_llm_provider(force_new=True).health()
        r.llm_reachable = bool(h.reachable)
        r.llm_soft = not r.llm_reachable
        if not r.llm_reachable:
            r.notes.append("LLM offline — fallback / Mock path works.")
    except Exception as e:
        r.llm_reachable = False
        r.llm_soft = True
        r.notes.append(f"LLM probe error (soft): {e}")

    # Native core
    try:
        from native_core.adapter import get_native_core

        nh = get_native_core().health()
        r.native_mode = str(nh.get("mode") or "python-fallback")
        r.native_available = bool(nh.get("available"))
    except Exception as e:
        r.native_mode = "unavailable"
        r.notes.append(f"native_core: {e}")

    # Security gate
    try:
        from security import safe_tool_call  # noqa: F401

        r.security_gate = True
    except Exception as e:
        r.security_gate = False
        r.blockers.append(f"critical: security gate missing: {e}")

    # SQLite storage
    try:
        from core.storage.sqlite_db import LeonSQLite

        db = LeonSQLite()
        st = db.stats()
        r.storage_sqlite = bool(st.get("schema_version"))
    except Exception:
        r.storage_sqlite = False
        r.notes.append("SQLite optional; JSON dual-read still primary for facts/graph.")

    if not r.api_ready:
        r.blockers.append("critical: API not importable")
    if not r.security_gate:
        r.blockers.append("critical: tool gate required before desktop agents")

    return r


def desktop_status() -> Dict[str, Any]:
    return desktop_readiness().to_dict()
