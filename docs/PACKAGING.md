# Leon packaging (Phase 11)

## Goal

Ship a **user-level Windows install** that starts Leon without requiring developers to know every module path.

## What Phase 11 delivers

| Item | Status |
|------|--------|
| `leon_desktop.py` entry | Yes |
| PyInstaller script | `scripts/build_windows.ps1` |
| NSIS installer script | `windows/Zenthon.nsi` |
| Portable CMD launchers | `windows/Leon.cmd`, `Leon-API.cmd` |
| Supervised local API | via `core.supervisor` |
| Tauri `.msi` / WebView2 product | **Not yet** (seed only) |

## Developer build

```powershell
.\scripts\build_windows.ps1
.\scripts\build_windows.ps1 -Installer   # requires NSIS
```

## End-user after install

1. Start **Leon** from Start Menu / Desktop shortcut → GUI + local API
2. Optional: React UI in browser after `npm run dev` in `ui/` (dev workflow)
3. Ollama offline is soft — app should still open

## Security

- Installer is **per-user** (`$LOCALAPPDATA`)
- API defaults to **127.0.0.1**
- Startup-with-Windows is **opt-in** section in NSIS

## Next (Phase 12)

E2E: install → launch → health → chat → shutdown → restart.
