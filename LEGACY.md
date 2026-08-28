# Legacy / optional layers

These packages are **not** the Leon cognitive core.

| Path | Role | Status |
|------|------|--------|
| `models/` | Classic ML/DL demos | Deprecated import warning |
| `training/` | Supervised trainers / losses | Deprecated import warning |
| `inference/predictors` | Model predictor | Optional |
| `inference/explainers` | SHAP/LIME helpers | Optional |
| `interfaces/web` | Old Flask UI | Deprecated → GUI/API |
| `inference/api/fastapi_app.py` | Re-exports cognitive app | Deprecated entry |
| `brain.core.Brain` | Thin stub | Keep for import compat |
| `brain.core_brain.ThinkingBrain` | LLM backend only | Internal to ReasoningEngine |
| `interfaces/gui` (Tkinter) | Functional desktop UI today | Legacy vs target React UI |

**Canonical path:** see `ARCHITECTURE.md` and `docs/PUBLIC_SURFACE.md`

```
interfaces → BrainOrchestrator → ReasoningEngine
  → knowledge.registry + memory + learning + curriculum
  → agents (react/coding) + security + omniverse
```

Do not import `models.*` or `training.*` from cognitive modules.

Deprecation helper: `from core.deprecation import warn_legacy, deprecated`

**Network:** FastAPI default bind is `127.0.0.1` (not `0.0.0.0`).
