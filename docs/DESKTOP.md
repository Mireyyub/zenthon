# Leon / Zenthon — Desktop path (Phase 8)

**Honest status:** hybrid *cognitive* core is ready to attach a thin shell.  
**Not yet:** single-click `Zenthon.exe` with Tauri + React.

---

## Today (working)

| Layer | Reality |
|-------|--------|
| Cognitive | Python ReasoningEngine + agents + curriculum |
| API | FastAPI `/api/v1/*` on **127.0.0.1** |
| LLM | `LLMProvider` (Ollama / Mock) |
| Storage | JSON primary + SQLite tasks |
| GUI | Tkinter (`interfaces/gui`) — legacy |
| Native | `native_core` optional binary; Python fallback always |
| Security | Gate + PathSandbox + allowlist |

Probe:

```bash
curl -s http://127.0.0.1:8000/api/v1/system/desktop | python -m json.tool
```

or:

```python
from native_core import desktop_status
print(desktop_status())
```

`ready_for_production_desktop` is always **false** until Tauri shell ships.  
`ready_for_tauri` is true when API + security gate import cleanly.

---

## Target (not implemented in Phase 8)

```
Tauri (Rust) window + tray
  → process supervisor (Python API, Ollama)
  → localhost FastAPI
  → same cognitive path
React/TS UI (no AI logic in browser)
```

Rules from ARCHITECTURE_AUDIT:

1. No AI reasoning in Rust or React
2. Default bind 127.0.0.1
3. Tools only via security gate
4. Offline-first; no silent network success

---

## Native core

- Ops: `normalize_text`, `fingerprint`, `token_metrics` only
- Env: `ZENTHON_NATIVE_CORE_BIN`
- Without binary → deterministic Python fallback

---

## Next phases (suggested)

| Phase | Focus |
|-------|--------|
| 9 | React + Vite client against `/api/v1` (no shell yet) |
| 10 | Tauri shell + supervisor seed |
| 11 | Windows packaging (Setup.exe) |
| 12 | E2E install → chat → shutdown |

---

*Phase 8 = readiness contract + RAG persist. No fake product claims.*
