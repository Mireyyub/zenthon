# Leon / Zenthon — Desktop path (Phase 8–9)

**Honest status:** hybrid *cognitive* core is ready to attach a thin shell.  
**Not yet:** single-click `Zenthon.exe` with Tauri + React packaging.

---

## Today (working)

| Layer | Reality |
|-------|--------|
| Cognitive | Python ReasoningEngine + agents + curriculum |
| API | FastAPI `/api/v1/*` on **127.0.0.1** |
| LLM | `LLMProvider` (Ollama / Mock) |
| Storage | JSON primary + SQLite tasks |
| GUI legacy | Tkinter (`interfaces/gui`) |
| GUI Phase 9 | React+Vite client in `ui/` → `/api/v1` only |
| Native | `native_core` optional binary; Python fallback always |
| Security | Gate + PathSandbox + allowlist |

Probe:

```bash
curl -s http://127.0.0.1:8000/api/v1/system/desktop | python -m json.tool
```

React UI:

```bash
# terminal 1
uvicorn interfaces.api.main:app --host 127.0.0.1 --port 8000
# terminal 2
cd ui && npm install && npm run dev
```

`ready_for_production_desktop` is always **false** until Tauri shell ships.  
`ready_for_tauri` is true when API + security gate import cleanly.

---

## Target (not implemented yet)

```
Tauri (Rust) window + tray
  → process supervisor (Python API, Ollama)
  → localhost FastAPI
  → same cognitive path
  → embed or load ui/ build
```

Rules from ARCHITECTURE_AUDIT:

1. No AI reasoning in Rust or React
2. Default bind 127.0.0.1
3. Tools only via security gate
4. Offline-first; no silent network success

---

## Next phases

| Phase | Focus |
|-------|--------|
| 10 | Tauri shell + supervisor seed |
| 11 | Windows packaging (Setup.exe) |
| 12 | E2E install → chat → shutdown |

---

*Phase 8 = readiness + RAG persist. Phase 9 = React API client. No fake product claims.*
