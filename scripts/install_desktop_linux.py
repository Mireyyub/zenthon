"""Install a local Zenthon desktop launcher and optional login autostart."""
from __future__ import annotations

import argparse
import os
import stat
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def write_desktop(target: Path, autostart: bool) -> None:
    launcher = ROOT / "scripts" / "launch_zenthon_desktop.sh"
    launcher.chmod(launcher.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    content = "\n".join(
        [
            "[Desktop Entry]",
            "Version=1.0",
            "Type=Application",
            "Name=Zenthon AI Platform",
            "Comment=Local AI desktop application",
            f"Exec={launcher}",
            f"Path={ROOT}",
            "Terminal=false",
            "Categories=Utility;Development;Science;",
            "StartupNotify=true",
            "X-GNOME-Autostart-enabled=true" if autostart else "",
        ]
    ).strip() + "\n"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    target.chmod(0o755)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--autostart", action="store_true", help="Sistemə daxil olarkən tətbiqi avtomatik başlat")
    parser.add_argument("--remove", action="store_true", help="Qısayol və autostart qeydlərini sil")
    args = parser.parse_args()
    app_file = Path.home() / ".local/share/applications/zenthon.desktop"
    auto_file = Path.home() / ".config/autostart/zenthon.desktop"
    if args.remove:
        for item in (app_file, auto_file):
            item.unlink(missing_ok=True)
        print("Zenthon masaüstü qısayolu silindi.")
        return
    write_desktop(app_file, autostart=False)
    if args.autostart:
        write_desktop(auto_file, autostart=True)
    print(f"Masaüstü tətbiq qısayolu yaradıldı: {app_file}")
    if args.autostart:
        print(f"Avtomatik başlanğıc aktivdir: {auto_file}")


if __name__ == "__main__":
    main()
