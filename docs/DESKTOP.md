# Leon / Zenthon — Desktop path (Phase 8–12)

**Honest status:** hybrid stack through packaging scripts + E2E smoke is in place.  
**Not claimed:** signed commercial Tauri store product.

---

## Stack map

| Phase | Deliverable |
|-------|-------------|
| 8 | Desktop readiness + RAG persist |
| 9 | React `/api/v1` client (`ui/`) |
| 10 | Process supervisor + Tauri seed |
| 11 | Windows PyInstaller/NSIS packaging |
| 12 | E2E smoke + manual checklist |

## Commands

```bash
# cognitive + API e2e
python scripts/e2e_desktop_smoke.py

# live supervisor child process
LEON_E2E_LIVE_SUPERVISOR=1 python scripts/e2e_desktop_smoke.py

# desktop entry (dev)
python leon_desktop.py

# Windows package (on Windows)
.\scripts\build_windows.ps1
```

## Probes

- `GET /api/v1/health`
- `GET /api/v1/system/desktop`
- `GET /api/v1/system/supervisor`

## Docs

- `docs/E2E.md` — automated + manual Windows checklist  
- `docs/PACKAGING.md` — installer scope  
- `windows/README.md` — build notes  

## Rules (unchanged)

1. No AI in Rust/React  
2. 127.0.0.1 default  
3. Security gate mandatory for tools  
4. Offline-first / soft LLM failure  
5. Claims = code  
