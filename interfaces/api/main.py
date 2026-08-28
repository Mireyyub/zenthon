"""
Leon FastAPI – cognitive + multimodal + crew endpoints.

Default bind is localhost only (security). Override for LAN:

    uvicorn interfaces.api.main:app --host 0.0.0.0 --port 8000

or:

    LEON_API_HOST=0.0.0.0 python -c "from interfaces.api.main import run; run()"

Canonical API surface (Phase 3+): /api/v1/*
Legacy routes at root remain for compatibility.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(
    title="Leon AI Platform",
    description=(
        "Cognitive API v0.7 prototype. "
        "Prefer /api/v1/* (Phase 3). Root routes are legacy-compatible."
    ),
    version="0.7.0",
)

# ── mount v1 gateway ─────────────────────────────────────────────
from interfaces.api.v1.router import api_v1_router  # noqa: E402

app.include_router(api_v1_router)


def _default_host() -> str:
    return os.getenv("LEON_API_HOST", os.getenv("ZENTHON_API_HOST", "127.0.0.1")).strip() or "127.0.0.1"


def _default_port() -> int:
    raw = os.getenv("LEON_API_PORT", os.getenv("ZENTHON_API_PORT", "8000")).strip()
    try:
        return int(raw)
    except ValueError:
        return 8000


class ThinkRequest(BaseModel):
    query: str
    goal: Optional[str] = None
    mode: str = "auto"
    agent: Optional[str] = None
    use_session: bool = False


class CycleRequest(BaseModel):
    query: str
    goal: Optional[str] = None
    image_path: Optional[str] = None
    audio_path: Optional[str] = None
    agent: Optional[str] = None
    learn: bool = True
    reflect: bool = True


class CrewRequest(BaseModel):
    goal: str
    mode: str = "sequential"
    agents: List[str] = Field(default_factory=lambda: ["react", "coding"])


class OrchestrateRequest(BaseModel):
    task: str
    agents: List[str] = Field(default_factory=lambda: ["react", "coding"])
    context: Dict[str, Any] = Field(default_factory=dict)


class SelfImproveRequest(BaseModel):
    topic: str = "general"
    apply: bool = False


class TeachRequest(BaseModel):
    lesson_id: Optional[str] = None
    volume_id: Optional[str] = "01"
    teach_volume: bool = False


class ReasonRequest(BaseModel):
    query: str
    strategy: str = "auto"
    goal: Optional[str] = None
    use_brain: bool = True


class MediaUnderstandRequest(BaseModel):
    path: str
    question: Optional[str] = None
    use_vlm: bool = True


class ImageGenerateRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=2000)
    width: int = Field(default=512, ge=32, le=2048)
    height: int = Field(default=512, ge=32, le=2048)
    style: str = "auto"
    seed: Optional[int] = None


class SpeechRequest(BaseModel):
    path: Optional[str] = None
    text: Optional[str] = None
    mode: str = "stt"  # stt | tts | status


@app.get("/")
def root() -> Dict[str, Any]:
    return {
        "name": "Leon",
        "version": "0.7.0",
        "bind_policy": "default 127.0.0.1 — set LEON_API_HOST to expose",
        "api_v1": "/api/v1",
        "legacy_endpoints": [
            "/health",
            "/status",
            "/native-core/status",
            "/think",
            "/reason",
            "/cycle",
            "/crew",
            "/orchestrate",
            "/self-improve/sync",
            "/teach",
            "/volumes",
            "/media/understand",
            "/media/generate",
            "/audio",
        ],
        "docs": "/docs",
        "public_surface": "docs/PUBLIC_SURFACE.md",
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


@app.get("/native-core/status")
def native_core_status() -> Dict[str, Any]:
    from native_core import health_report

    return health_report()


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


@app.post("/cycle")
def cycle_endpoint(req: CycleRequest) -> Dict[str, Any]:
    try:
        from brain.cognitive_cycle import CognitiveCycle

        return CognitiveCycle().run(
            req.query,
            goal=req.goal,
            image_path=req.image_path,
            audio_path=req.audio_path,
            agent_type=req.agent,
            learn=req.learn,
            reflect=req.reflect,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/crew")
def crew_endpoint(req: CrewRequest) -> Dict[str, Any]:
    try:
        from agents.crew import run_crew

        tasks = [{"description": req.goal, "agent": a} for a in (req.agents or ["react"])]
        return run_crew(req.goal, tasks, mode=req.mode)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/orchestrate")
def orchestrate_endpoint(req: OrchestrateRequest) -> Dict[str, Any]:
    try:
        from agents.unified_orchestrator import unified_orchestrator

        return unified_orchestrator.run(req.task, agents=req.agents, context=req.context)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/self-improve/sync")
def self_improve_sync_endpoint(req: SelfImproveRequest) -> Dict[str, Any]:
    try:
        from brain.self_learning_sync import sync_self_learning

        return sync_self_learning(topic=req.topic, apply=req.apply)
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


@app.post("/media/understand")
def media_understand(req: MediaUnderstandRequest) -> Dict[str, Any]:
    try:
        from multimodal.understand import understand_image

        return understand_image(
            req.path, question=req.question, use_vlm=req.use_vlm, inject_facts=False
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/media/generate")
def media_generate(req: ImageGenerateRequest) -> Dict[str, Any]:
    try:
        from multimodal.generate import generate_image

        return generate_image(
            req.prompt, width=req.width, height=req.height, style=req.style, seed=req.seed
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/audio")
def audio_endpoint(req: SpeechRequest) -> Dict[str, Any]:
    try:
        from multimodal.audio import understand_speech, generate_speech, audio_available

        if req.mode == "status":
            return audio_available()
        if req.mode == "stt":
            if not req.path:
                raise HTTPException(status_code=400, detail="path required for stt")
            return understand_speech(req.path)
        if req.mode == "tts":
            return generate_speech(req.text or "")
        return audio_available()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def run(host: Optional[str] = None, port: Optional[int] = None) -> None:
    """Start uvicorn. Defaults: 127.0.0.1:8000 (not 0.0.0.0)."""
    import uvicorn

    h = host if host is not None else _default_host()
    p = port if port is not None else _default_port()
    uvicorn.run("interfaces.api.main:app", host=h, port=p, reload=False)


if __name__ == "__main__":
    run()
