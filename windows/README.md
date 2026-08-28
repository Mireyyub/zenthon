# Windows packaging (Phase 11)

## Artifacts

| Output | How |
|--------|-----|
| `dist/Zenthon/Zenthon.exe` | `scripts/build_windows.ps1` |
| `dist/Zenthon-Setup.exe` | `scripts/build_windows.ps1 -Installer` (needs NSIS) |
| `windows/Leon.cmd` | Portable / post-install launcher |
| `windows/Leon-API.cmd` | API-only supervised process |

## Build (on Windows 11)

```powershell
# from repo root
.\scripts\build_windows.ps1
# with NSIS installer:
.\scripts\build_windows.ps1 -Installer
```

## Runtime

- Default API bind: **127.0.0.1:8000**
- GUI: Tkinter (current)
- React UI: separate `cd ui && npm run dev` (not bundled as production webview yet)
- Env:
  - `LEON_DESKTOP_NO_API=1` — skip supervisor
  - `LEON_OPEN_UI=1` — open browser to UI URL
  - `LEON_UI_URL` — default `http://127.0.0.1:5173`

## Honest limits

- This is **PyInstaller + NSIS**, not full Tauri product packaging.
- `desktop/tauri` remains a seed until Phase 10 toolchain is completed in CI.
- Do not market as single-click AGI desktop.

See `docs/PACKAGING.md`.
