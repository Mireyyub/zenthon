"""
LEGACY FastAPI entry (ML-era).

Deprecated for cognitive Leon endpoints.
Use instead:

    uvicorn interfaces.api.main:app --host 127.0.0.1 --port 8000

This module re-exports the cognitive app when possible so old commands still work.
"""

from __future__ import annotations

from core.deprecation import warn_legacy

warn_legacy(
    "inference.api.fastapi_app is deprecated. "
    "Use: uvicorn interfaces.api.main:app --host 127.0.0.1 --port 8000",
    stacklevel=1,
)

try:
    from interfaces.api.main import app, run
except Exception:
    # fallback minimal app if cognitive import fails
    from fastapi import FastAPI

    app = FastAPI(title="Leon LEGACY – prefer interfaces.api.main", version="0.7.0-legacy")

    @app.get("/health")
    def _health():
        return {
            "ok": False,
            "deprecated": True,
            "message": "Use uvicorn interfaces.api.main:app",
        }

    def run(host: str = "127.0.0.1", port: int = 8000):
        import uvicorn

        uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run()
