# Leon E2E — Phase 12

## Automated (CI / any OS)

```bash
python scripts/e2e_desktop_smoke.py
# optional live uvicorn child:
LEON_E2E_LIVE_SUPERVISOR=1 LEON_E2E_PORT=8765 python scripts/e2e_desktop_smoke.py
```

Covers:

1. Bootstrap  
2. `GET /api/v1/health`  
3. `GET /api/v1/system/desktop` (honest `ready_for_production_desktop=false`)  
4. `GET /api/v1/system/supervisor`  
5. `POST /api/v1/chat`  
6. `POST /api/v1/reason`  
7. `leon_desktop` import (launch entry)  
8. Optional: supervisor start → health → chat → stop → restart → stop  

## Manual Windows checklist (after Phase 11 build)

| # | Action | Expect |
|---|--------|--------|
| 1 | `build_windows.ps1` | `dist/Zenthon/Zenthon.exe` exists |
| 2 | Run `Zenthon.exe` | GUI opens; no crash |
| 3 | `curl http://127.0.0.1:8000/api/v1/health` | 200 JSON |
| 4 | Chat in GUI or `POST /api/v1/chat` | Answer / confidence |
| 5 | Close GUI | Process exits; API stops (atexit) |
| 6 | Run again | Second launch works |
| 7 | Optional `-Installer` | `Zenthon-Setup.exe` installs under `%LOCALAPPDATA%\Programs\Leon` |
| 8 | Uninstall | Shortcuts + dir removed |

## Out of scope (honest)

- Full Tauri WebView product E2E  
- Code-signed commercial cert  
- Auto-update channel  

## Related

- `docs/PACKAGING.md`  
- `docs/DESKTOP.md`  
- `scripts/smoke_test.py` (cognitive bootstrap smoke)  
