# Leon Desktop (Phase 10)

## What exists

| Piece | Path | Status |
|-------|------|--------|
| Process supervisor | `core/supervisor.py` | **Working** (Python) |
| Supervised API runner | `scripts/run_supervised_api.py` | **Working** |
| Tauri shell seed | `desktop/tauri/` | **Seed only** — needs Rust + Tauri CLI to build |
| React UI | `ui/` | Phase 9 client |

## Rules

1. **No AI reasoning in Rust or React**
2. Supervisor only manages **API process** + soft Ollama probe
3. Default bind **127.0.0.1**
4. Do not claim production `.exe` until Phase 11 packaging

## Run API under supervisor

```bash
python scripts/run_supervised_api.py
# or
python -m core.supervisor
```

Then UI:

```bash
cd ui && npm run dev
```

## Tauri seed

```bash
cd desktop/tauri
# requires: rustup, cargo, tauri-cli
# cargo tauri dev   # when toolchain installed
```

The seed opens a webview to `http://127.0.0.1:5173` (dev UI) or configured URL.
It does **not** embed ReasoningEngine.

## Status API

```bash
curl -s http://127.0.0.1:8000/api/v1/system/supervisor
```
