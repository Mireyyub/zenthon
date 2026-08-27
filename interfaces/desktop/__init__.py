"""Desktop runtime composition for the local-first Zenthon application."""

__all__ = ["DesktopRuntime", "run_desktop"]


def __getattr__(name: str):
    if name in __all__:
        from interfaces.desktop.runtime import DesktopRuntime, run_desktop

        return {"DesktopRuntime": DesktopRuntime, "run_desktop": run_desktop}[name]
    raise AttributeError(name)
