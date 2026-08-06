# Legacy / optional layers

These packages are **not** the Leon cognitive core. They remain for historical ML experiments.

| Path | Role |
|------|------|
| `models/` | Classic ML/DL demos (sklearn/torch) |
| `training/` | Supervised trainers / losses |
| `inference/predictors` | Model predictor |
| `inference/explainers` | SHAP/LIME helpers |
| `interfaces/web/web_interface.py` | Old Flask UI – prefer GUI/API |
| `inference/api/fastapi_app.py` | Deprecated; re-exports `interfaces.api.main` |

**Canonical cognitive path**

```
interfaces → brain.orchestrator → reasoning.engine
  → knowledge + memory + learning + curriculum
  → agents (react/coding) + security + omniverse
```

Do not import `models.*` from cognitive modules.
