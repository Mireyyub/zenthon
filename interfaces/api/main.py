"""
Leon FastAPI – cognitive endpoints (Faza 7).

    uvicorn interfaces.api.main:app --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(
    title="Leon AI Platform",
    description="Cognitive API: think / teach / status / health",
    version="0.7.0",
)


class ThinkRequest(BaseModel):
    query: str
    goal: Optional[str] = None
    mode: str = "auto"
    agent: Optional[str] = None
    use_session: bool = False


class TeachRequest(BaseModel):
    lesson_id: Optional[str] = None
    volume_id: Optional[str] = "01"
    teach_volume: bool = False


class ReasonRequest(BaseModel):
    query: str
    strategy: str = "auto"
    goal: Optional[str] = None
    use_brain: bool = True


@app.get("/")
def root() -> Dict[str, Any]:
    return {
        "name": "Leon",
        "endpoints": ["/health", "/status", "/think", "/reason", "/teach"],
    }


@app.get("/health")
def health() -> Dict[str, Any]:
    from interfaces.api.health import health_report

    return health_report()


@app.get("/status")
def status() -> Dict[str, Any]:
    try:
        from core.bootstrap import leon_status

        return leon_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/think")
def think(req: ThinkRequest) -> Dict[str, Any]:
    try:
        from brain.orchestrator import BrainOrchestrator
        from core.config import config

        orch = BrainOrchestrator(brain_name=getattr(config, "ai_name", "Leon") or "Leon")
        result = orch.run(
            req.query,
            goal=req.goal,
            reasoning_mode=req.mode,
            agent_type=req.agent,
            use_session=req.use_session,
        )
        return {
            "answer": result.get("answer") or result.get("conclusion"),
            "confidence": result.get("confidence"),
            "confidence_label": result.get("confidence_label"),
            "source": result.get("source"),
            "trace_id": result.get("trace_id"),
            "decision": result.get("decision"),
            "evidence": result.get("evidence"),
            "llm_used": result.get("llm_used"),
            "agent": result.get("agent"),
            "reasoning_mode": result.get("reasoning_mode"),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/reason")
def reason(req: ReasonRequest) -> Dict[str, Any]:
    try:
        from brain.reasoning.engine import reasoning_engine

        return reasoning_engine.reason(
            req.query,
            strategy=req.strategy,
            goal=req.goal,
            use_brain=req.use_brain,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/teach")
def teach(req: TeachRequest) -> Dict[str, Any]:
    try:
        from curriculum import CurriculumEngine
        from core.bootstrap import save_state

        eng = CurriculumEngine()
        if req.teach_volume or (req.volume_id and not req.lesson_id):
            report = eng.teach_volume(req.volume_id or "01")
        else:
            report = eng.teach(req.lesson_id or "000001", volume_id=req.volume_id)
        try:
            save_state("api_teach")
        except Exception:
            pass
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/volumes")
def volumes() -> Dict[str, Any]:
    try:
        from curriculum import CurriculumEngine, load_volume

        eng = CurriculumEngine()
        items = []
        for vid in eng.list_volumes():
            try:
                items.append(load_volume(vid))
            except Exception as e:
                items.append({"volume": vid, "error": str(e)})
        return {"volumes": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def run(host: str = "0.0.0.0", port: int = 8000) -> None:
    import uvicorn

    uvicorn.run("interfaces.api.main:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    run()
