# Leon UI (Phase 9)

React + Vite + TypeScript client for **Leon `/api/v1` only**.

## Rules

- **No AI logic in the browser** — reasoning stays on the Python backend.
- **No unrestricted FS / shell** from the UI.
- Default API: `http://127.0.0.1:8000` (via Vite proxy in dev).

## Run

Terminal 1 — backend:

```bash
python -m uvicorn interfaces.api.main:app --host 127.0.0.1 --port 8000
```

Terminal 2 — UI:

```bash
cd ui
npm install
npm run dev
```

Open `http://127.0.0.1:5173`.

Optional: `VITE_LEON_API=http://127.0.0.1:8000` if not using the proxy.

## What it does

| Screen | API |
|--------|-----|
| Chat | `POST /api/v1/chat` |
| Health / LLM / Desktop / Agents | `GET /api/v1/health`, `/system/desktop`, `/models`, `/agents` |

## Not included (later phases)

- Tauri shell
- Full task board / knowledge browser
- Streaming token UI
- Auth

See `docs/UI.md` and `docs/DESKTOP.md`.
