"""Windows/PyInstaller entry point for the Zenthon desktop application."""
from __future__ import annotations

from interfaces.gui.main_gui import run_gui


if __name__ == "__main__":
    run_gui()
