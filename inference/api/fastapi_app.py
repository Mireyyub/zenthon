"""
FastAPI Application Module
REST API for serving AI models using FastAPI.
"""

import os
import json
import numpy as np
import torch
from typing import Optional, Dict, Any, List, Union
from fastapi import FastAPI, HTTPException, Request, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
import uvicorn

from core.logger import logger
from core.config import config
from inference.predictors.model_predictor import ModelPredictor, ImagePredictor
from inference.explainers.lime_explainer import LIMEExplainer


# Initialize FastAPI app
app = FastAPI(
    title="AI System API",
    description="REST API for AI System - Model Serving and Inference",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global model registry
MODEL_REGISTRY = {}
PREDICTOR_REGISTRY = {}
EXPLAINER_REGISTRY = {}


class PredictionRequest(BaseModel):
    """Request model for predictions."""
    model_name: str
    data: Union[List[List[float]], Dict[str, Any]]
    explain: bool = False


class PredictionResponse(BaseModel):
    """Response model for predictions."""
    model_name: str
    prediction: Any
    explanation: Optional[Dict[str, Any]] = None
    processing_time: float


class ModelInfo(BaseModel):
    """Model information model."""
    name: str
    type: str
    input_shape: Optional[List[int]] = None
    output_shape: Optional[List[int]] = None
    description: Optional[str] = None


# Load models from config
@app.on_event("startup")
async def startup_event():
    """Initialize models on startup."""
    logger.info("Starting AI System API...")
    logger.info(f"Base directory: {config.path.base_dir}")
    logger.info(f"Models directory: {config.path.models_dir}")

    # Load any saved models from the models directory
    try:
        if os.path.exists(config.path.saved_models_dir):
            for model_file in os.listdir(config.path.saved_models_dir):
                if model_file.endswith(".pt") or model_file.endswith(".pth"):
                    model_name = model_file.replace(".pt", "").replace(".pth", "")
                    try:
                        # Load PyTorch model
                        model_path = os.path.join(config.path.saved_models_dir, model_file)
                        model = torch.load(model_path, map_location="cpu")
                        MODEL_REGISTRY[model_name] = model
                        PREDICTOR_REGISTRY[model_name] = ModelPredictor(
                            model=model,
                            model_type="pytorch",
                        )
                        logger.info(f"Loaded model: {model_name}")
                    except Exception as e:
                        logger.error(f"Failed to load model {model_file}: {e}")
    except Exception as e:
        logger.error(f"Error loading models: {e}")

    logger.info("AI System API started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down AI System API...")
    MODEL_REGISTRY.clear()
    PREDICTOR_REGISTRY.clear()
    EXPLAINER_REGISTRY.clear()
    logger.info("AI System API shutdown complete")


@app.get("/", tags=["General"])
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to AI System API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", tags=["General"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "models_loaded": len(MODEL_REGISTRY),
        "predictors_loaded": len(PREDICTOR_REGISTRY),
    }


@app.get("/models", tags=["Models"], response_model=List[ModelInfo])
async def list_models():
    """List all available models."""
    models = []
    for name, model in MODEL_REGISTRY.items():
        model_info = ModelInfo(
            name=name,
            type="pytorch",
            description=f"Model {name}",
        )
        models.append(model_info)
    return models


@app.post("/register_model", tags=["Models"])
async def register_model(
    model_name: str,
    model_type: str = "pytorch",
    model_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Register a new model.
    
    Args:
        model_name: Name of the model.
        model_type: Type of the model ('pytorch', 'sklearn').
        model_path: Path to the model file.
    """
    try:
        if model_path:
            # Load model from file
            if model_type == "pytorch":
                model = torch.load(model_path, map_location="cpu")
            else:
                import joblib
                model = joblib.load(model_path)
        else:
            # For now, just store the model name
            model = None

        MODEL_REGISTRY[model_name] = model
        PREDICTOR_REGISTRY[model_name] = ModelPredictor(
            model=model,
            model_type=model_type,
        )

        logger.info(f"Registered model: {model_name}")
        return {"status": "success", "model_name": model_name}
    except Exception as e:
        logger.error(f"Failed to register model {model_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/predict", tags=["Prediction"], response_model=PredictionResponse)
async def predict(request: PredictionRequest) -> PredictionResponse:
    """
    Make a prediction using a registered model.
    
    Args:
        request: PredictionRequest containing model_name and data.
    """
    import time

    start_time = time.time()

    try:
        # Get predictor
        if request.model_name not in PREDICTOR_REGISTRY:
            raise HTTPException(
                status_code=404,
                detail=f"Model {request.model_name} not found. Available models: {list(PREDICTOR_REGISTRY.keys())}"
            )

        predictor = PREDICTOR_REGISTRY[request.model_name]

        # Make prediction
        prediction = predictor.predict(request.data)

        # Generate explanation if requested
        explanation = None
        if request.explain:
            if request.model_name in EXPLAINER_REGISTRY:
                explainer = EXPLAINER_REGISTRY[request.model_name]
                explanation = explainer.explain_instance(request.data)
            else:
                # Create a temporary explainer
                explainer = LIMEExplainer(
                    model=predictor.model,
                    feature_names=None,
                )
                explanation = explainer.explain_instance(request.data)

        processing_time = time.time() - start_time

        return PredictionResponse(
            model_name=request.model_name,
            prediction=prediction,
            explanation=explanation,
            processing_time=processing_time,
        )

    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/predict_image", tags=["Prediction"])
async def predict_image(
    model_name: str,
    file: UploadFile = File(...),
    explain: bool = False,
) -> Dict[str, Any]:
    """
    Make a prediction on an image.
    
    Args:
        model_name: Name of the model.
        file: Image file to predict on.
        explain: Whether to generate explanation.
    """
    import time
    from PIL import Image

    start_time = time.time()

    try:
        # Get predictor
        if model_name not in PREDICTOR_REGISTRY:
            raise HTTPException(
                status_code=404,
                detail=f"Model {model_name} not found. Available models: {list(PREDICTOR_REGISTRY.keys())}"
            )

        predictor = PREDICTOR_REGISTRY[model_name]

        # Check if it's an image predictor
        if not isinstance(predictor, ImagePredictor):
            # Try to convert to ImagePredictor
            image_predictor = ImagePredictor(
                model=predictor.model,
                model_type=predictor.model_type,
                device=predictor.device,
            )
        else:
            image_predictor = predictor

        # Read and preprocess image
        image = Image.open(file.file)
        image = np.array(image)

        # Make prediction
        prediction = image_predictor.predict_image(image)

        # Generate explanation if requested
        explanation = None
        if explain:
            # For image explanations, we'd need a specialized explainer
            # This is a placeholder
            explanation = {"message": "Image explanation not implemented"}

        processing_time = time.time() - start_time

        return {
            "model_name": model_name,
            "prediction": prediction,
            "explanation": explanation,
            "processing_time": processing_time,
        }

    except Exception as e:
        logger.error(f"Image prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/explain", tags=["Explanation"])
async def explain(
    model_name: str,
    data: Union[List[List[float]], Dict[str, Any]],
    method: str = "lime",
) -> Dict[str, Any]:
    """
    Generate explanation for a prediction.
    
    Args:
        model_name: Name of the model.
        data: Input data to explain.
        method: Explanation method ('lime', 'shap').
    """
    try:
        if model_name not in MODEL_REGISTRY:
            raise HTTPException(
                status_code=404,
                detail=f"Model {model_name} not found"
            )

        model = MODEL_REGISTRY[model_name]

        # Create explainer based on method
        if method.lower() == "lime":
            from inference.explainers.lime_explainer import LIMEExplainer
            explainer = LIMEExplainer(model=model)
        elif method.lower() == "shap":
            from inference.explainers.shap_explainer import KernelSHAP
            explainer = KernelSHAP(model=model)
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown explanation method: {method}. Use 'lime' or 'shap'."
            )

        # Generate explanation
        explanation = explainer.explain_instance(data)

        return {
            "model_name": model_name,
            "method": method,
            "explanation": explanation,
        }

    except Exception as e:
        logger.error(f"Explanation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/register_explainer", tags=["Explanation"])
async def register_explainer(
    model_name: str,
    method: str = "lime",
    feature_names: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Register an explainer for a model.
    
    Args:
        model_name: Name of the model.
        method: Explanation method ('lime', 'shap').
        feature_names: Names of input features.
    """
    try:
        if model_name not in MODEL_REGISTRY:
            raise HTTPException(
                status_code=404,
                detail=f"Model {model_name} not found"
            )

        model = MODEL_REGISTRY[model_name]

        # Create explainer based on method
        if method.lower() == "lime":
            from inference.explainers.lime_explainer import LIMEExplainer
            explainer = LIMEExplainer(
                model=model,
                feature_names=feature_names,
            )
        elif method.lower() == "shap":
            from inference.explainers.shap_explainer import KernelSHAP
            explainer = KernelSHAP(
                model=model,
                feature_names=feature_names,
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown explanation method: {method}"
            )

        EXPLAINER_REGISTRY[model_name] = explainer

        logger.info(f"Registered explainer for model {model_name} using {method}")
        return {"status": "success", "model_name": model_name, "method": method}

    except Exception as e:
        logger.error(f"Failed to register explainer: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def run_api(
    host: str = "0.0.0.0",
    port: int = 8000,
    log_level: str = "info",
) -> None:
    """
    Run the FastAPI application.
    
    Args:
        host: Host address.
        port: Port number.
        log_level: Logging level.
    """
    uvicorn.run(
        "inference.api.fastapi_app:app",
        host=host,
        port=port,
        log_level=log_level,
        reload=False,
    )


if __name__ == "__main__":
    run_api()
