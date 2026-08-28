# Leon UI — Phase 9

**Stack:** React 18 + Vite 5 + TypeScript  
**Path:** `ui/`  
**Contract:** HTTP client for `/api/v1` only.

## Boundaries

| Allowed | Forbidden |
|---------|-----------|
| Call FastAPI `/api/v1/*` | Local reasoning / LLM in JS |
| Show confidence, source, trace_id | Tool execution from browser |
| Desktop readiness display | Unrestricted FS / shell |
| Vite proxy to 127.0.0.1:8000 | Claiming production desktop |

## Dev

```bash
# backend
uvicorn interfaces.api.main:app --host 127.0.0.1 --port 8000

# ui
cd ui && npm install && npm run dev
```

CORS allows `http://127.0.0.1:5173` and `http://localhost:5173`.

## Relation to desktop roadmap

- **Today UI:** Tkinter (legacy) + this React client (dev)
- **Target shell:** Tauri (Phase 10+) embedding or loading this UI
- `ready_for_production_desktop` remains **false** until packaging ships

## Honest scope

Phase 9 delivers a **working chat + status client**, not a full product dashboard.
