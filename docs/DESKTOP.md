# Leon / Zenthon — Desktop path (Phase 8–11)

**Honest status:** cognitive core + API + React client + supervisor + **Windows PyInstaller/NSIS packaging scripts** exist.  
**Not yet:** polished single-click Tauri commercial installer.

---

## Today

| Layer | Reality |
|-------|--------|
| Cognitive | Python ReasoningEngine + agents |
| API | FastAPI `/api/v1` on 127.0.0.1 |
| Supervisor | `core/supervisor.py` |
| Desktop entry | `leon_desktop.py` / `Zenthon.exe` |
| Packaging | `scripts/build_windows.ps1` + `windows/Zenthon.nsi` |
| GUI | Tkinter primary; React in `ui/` |
| Tauri | Seed under `desktop/tauri/` |

### Dev run

```bash
python leon_desktop.py
# or API only
python scripts/run_supervised_api.py
```

### Windows build

```powershell
.\scripts\build_windows.ps1
.\scripts\build_windows.ps1 -Installer
```

See `docs/PACKAGING.md` and `windows/README.md`.

---

## Rules

1. No AI in Rust/React  
2. Default bind 127.0.0.1  
3. Tools via security gate  
4. Offline-first  
5. Packaging claims match scripts (PyInstaller path now; Tauri later)

---

## Next

| Phase | Focus |
|-------|--------|
| **12** | E2E install → chat → shutdown → restart checklist + smoke |
