# Leon / Zenthon — Desktop path (Phase 8–10)

**Honest status:** cognitive core + API + React client + **Python process supervisor** work.  
**Not yet:** production Tauri `.exe` installer (Phase 11).

---

## Today (working)

| Layer | Reality |
|-------|--------|
| Cognitive | Python ReasoningEngine + agents + curriculum |
| API | FastAPI `/api/v1/*` on **127.0.0.1** |
| Supervisor | `core/supervisor.py` — start/stop/restart uvicorn |
| LLM | `LLMProvider` (Ollama soft probe) |
| Storage | JSON primary + SQLite tasks |
| GUI legacy | Tkinter |
| GUI Phase 9 | `ui/` React → `/api/v1` |
| Shell Phase 10 | `desktop/tauri/` **seed** (no full Tauri dependency required to develop) |
| Native | `native_core` optional helpers |
| Security | Gate + PathSandbox + allowlist |

### Supervised API

```bash
python scripts/run_supervised_api.py
# or
python -m core.supervisor
```

### UI

```bash
cd ui && npm install && npm run dev
```

### Probes

```bash
curl -s http://127.0.0.1:8000/api/v1/system/desktop
curl -s http://127.0.0.1:8000/api/v1/system/supervisor
```

---

## Tauri seed (`desktop/tauri/`)

- Documents window + CSP + frontendDist toward `ui/dist`
- `src/main.rs` prints JSON seed status — **ai_in_rust: false**
- Real `tauri::Builder` when Rust toolchain + `tauri-cli` installed
- Sidecar target: `python -m core.supervisor`

---

## Rules

1. No AI reasoning in Rust or React  
2. Default bind 127.0.0.1  
3. Tools only via security gate  
4. Offline-first; Ollama offline is soft  
5. `ready_for_production_desktop` stays **false** until Phase 11 packaging

---

## Next

| Phase | Focus |
|-------|--------|
| **11** | Windows packaging (Setup / single entry) |
| **12** | E2E install → chat → shutdown → restart |

---

*Phase 10 = supervisor + Tauri seed. Not a fake product binary.*
