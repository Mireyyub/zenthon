"""Optional native acceleration boundary with deterministic Python fallbacks."""

from native_core.adapter import NativeCore, get_native_core, health_report
from native_core.desktop import DesktopReadiness, desktop_readiness, desktop_status

__all__ = [
    "NativeCore",
    "get_native_core",
    "health_report",
    "DesktopReadiness",
    "desktop_readiness",
    "desktop_status",
]
