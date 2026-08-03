"""
LEGACY FastAPI entry (ML-era).

Deprecated for cognitive Leon endpoints.
Use instead:

    uvicorn interfaces.api.main:app --host 0.0.0.0 --port 8000

This module re-exports the cognitive app when possible so old commands still work.
"""

from __future__ import annotations

try:
    from interfaces.api.main import app, run
except Exception:
    # fallback minimal app if cognitive import fails
    from fastapi import FastAPI

    app = FastAPI(title="Leon LEGACY – prefer interfaces.api.main")

    @app.get("/health")
    def _health():
        return {
            "ok": False,
            "deprecated": True,
            "message": "Use uvicorn interfaces.api.main:app",
        }

    def run(host: str = "0.0.0.0", port: int = 8000):
        import uvicorn

        uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run()
