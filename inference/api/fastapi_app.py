"""
FastAPI – Model serving + Leon /think endpoint.
"""

import os
import time
from typing import Optional, Dict, Any, List, Union

from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from core.logger import logger
from core.config import config

app = FastAPI(
    title="Leon AI Platform API",
    description="Model inference + Leon Cognitive Brain API",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MODEL_REGISTRY: Dict[str, Any] = {}
PREDICTOR_REGISTRY: Dict[str, Any] = {}
EXPLAINER_REGISTRY: Dict[str, Any] = {}
_orchestrator = None


def get_orchestrator():
    global _orchestrator
    if _orchestrator is None:
        from brain.orchestrator import BrainOrchestrator
        _orchestrator = BrainOrchestrator(brain_name="Leon")
    return _orchestrator


class PredictionRequest(BaseModel):
    model_name: str
    data: Union[List[List[float]], Dict[str, Any]]
    explain: bool = False


class PredictionResponse(BaseModel):
    model_name: str
    prediction: Any
    explanation: Optional[Dict[str, Any]] = None
    processing_time: float


class ThinkRequest(BaseModel):
    query: str
    goal: Optional[str] = None
    reasoning_mode: str = "auto"
    agent_type: Optional[str] = None


class ThinkResponse(BaseModel):
    cycle: int
    reasoning_mode: str
    confidence: float
    conclusion: Any
    decision: Dict[str, Any]
    llm_used: bool = False
    reflection: Optional[Dict[str, Any]] = None
    agent: Optional[Dict[str, Any]] = None
    processing_time: float


@app.on_event("startup")
async def startup_event():
    logger.info("Leon API starting...")
    try:
        import torch
        if os.path.exists(getattr(config.path, "saved_models_dir", "models/saved")):
            saved_dir = config.path.saved_models_dir
            if os.path.isdir(saved_dir):
                for model_file in os.listdir(saved_dir):
                    if model_file.endswith((".pt", ".pth")):
                        name = model_file.rsplit(".", 1)[0]
                        try:
                            path = os.path.join(saved_dir, model_file)
                            model = torch.load(path, map_location="cpu")
                            MODEL_REGISTRY[name] = model
                            from inference.predictors.model_predictor import ModelPredictor
                            PREDICTOR_REGISTRY[name] = ModelPredictor(model=model, model_type="pytorch")
                            logger.info(f"Loaded model: {name}")
                        except Exception as e:
                            logger.error(f"Load failed {model_file}: {e}")
    except Exception as e:
        logger.debug(f"Model load skip: {e}")
    logger.info("Leon API ready.")


@app.on_event("shutdown")
async def shutdown_event():
    MODEL_REGISTRY.clear()
    PREDICTOR_REGISTRY.clear()
    logger.info("Leon API shutdown.")


@app.get("/")
async def root():
    return {
        "message": "Leon AI Platform API",
        "version": "2.0.0",
        "docs": "/docs",
        "endpoints": ["/health", "/think", "/predict", "/models", "/status"],
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "ai": "Leon",
        "models_loaded": len(MODEL_REGISTRY),
        "brain": "ready",
    }


@app.post("/think", response_model=ThinkResponse, tags=["Brain"])
async def think(req: ThinkRequest):
    start = time.time()
    try:
        orch = get_orchestrator()
        result = orch.run(
            req.query,
            goal=req.goal,
            reasoning_mode=req.reasoning_mode,
            agent_type=req.agent_type,
        )
        return ThinkResponse(
            cycle=result.get("cycle", 0),
            reasoning_mode=result.get("reasoning_mode", "auto"),
            confidence=float(result.get("confidence", 0)),
            conclusion=result.get("conclusion"),
            decision=result.get("decision") or {},
            llm_used=bool(result.get("llm_used")),
            reflection=result.get("reflection"),
            agent=result.get("agent"),
            processing_time=round(time.time() - start, 3),
        )
    except Exception as e:
        logger.error(f"/think failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/status", tags=["Brain"])
async def brain_status():
    try:
        orch = get_orchestrator()
        return orch.status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/models", tags=["Models"])
async def list_models():
    return [{"name": n, "type": "registered"} for n in MODEL_REGISTRY]


@app.post("/predict", response_model=PredictionResponse, tags=["Prediction"])
async def predict(request: PredictionRequest):
    start = time.time()
    if request.model_name not in PREDICTOR_REGISTRY:
        raise HTTPException(404, f"Model not found: {request.model_name}")
    try:
        predictor = PREDICTOR_REGISTRY[request.model_name]
        prediction = predictor.predict(request.data)
        explanation = None
        if request.explain:
            try:
                from inference.explainers.lime_explainer import LIMEExplainer
                explainer = LIMEExplainer(model=predictor.model, feature_names=None)
                explanation = explainer.explain_instance(request.data)
            except Exception:
                explanation = {"message": "explanation unavailable"}
        return PredictionResponse(
            model_name=request.model_name,
            prediction=prediction,
            explanation=explanation,
            processing_time=round(time.time() - start, 3),
        )
    except Exception as e:
        raise HTTPException(500, str(e))


def run_api(host: str = "0.0.0.0", port: int = 8000, log_level: str = "info") -> None:
    uvicorn.run("inference.api.fastapi_app:app", host=host, port=port, log_level=log_level, reload=False)


if __name__ == "__main__":
    run_api()
