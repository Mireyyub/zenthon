"""
Vision describe via Ollama native API (llava / moondream / bakllava).
Soft-fail when model or server missing.
"""

from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.logger import logger


def _ollama_base() -> str:
    try:
        from core.config import config

        return config.llm.base_url.replace("/v1", "").rstrip("/")
    except Exception:
        return "http://localhost:11434"


def _vision_models_preference() -> List[str]:
    import os

    env = os.environ.get("LEON_VISION_MODEL") or os.environ.get("ZENTHON_VISION_MODEL")
    preferred = []
    if env:
        preferred.append(env)
    preferred.extend(
        [
            "llava",
            "llava:latest",
            "llava:7b",
            "moondream",
            "moondream:latest",
            "bakllava",
            "llama3.2-vision",
            "llama3.2-vision:latest",
        ]
    )
    return preferred


def vision_available() -> Dict[str, Any]:
    import urllib.request

    base = _ollama_base()
    try:
        req = urllib.request.Request(f"{base}/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        names = [m.get("name", "") for m in data.get("models", [])]
        hit = None
        for pref in _vision_models_preference():
            for n in names:
                if n == pref or n.startswith(pref.split(":")[0]):
                    hit = n
                    break
            if hit:
                break
        return {
            "reachable": True,
            "models": names,
            "vision_model": hit,
            "ready": hit is not None,
            "hint": None
            if hit
            else "Ollama-da vision model çəkin: ollama pull llava  və ya  ollama pull moondream",
        }
    except Exception as e:
        return {
            "reachable": False,
            "ready": False,
            "vision_model": None,
            "models": [],
            "error": str(e),
            "hint": "ollama serve işləmir və ya host yanlışdır",
        }


def _encode_image(path: str | Path) -> str:
    p = Path(path).expanduser().resolve()
    if not p.exists():
        raise FileNotFoundError(str(p))
    return base64.b64encode(p.read_bytes()).decode("ascii")


def describe_image(
    path: str,
    prompt: str = "Bu şəkli qısa və dəqiq təsvir et. Obyektlər, rənglər, səhnə.",
    model: Optional[str] = None,
) -> Dict[str, Any]:
    """Ollama /api/generate with images=[b64]."""
    import urllib.request

    status = vision_available()
    use_model = model or status.get("vision_model")
    if not status.get("reachable"):
        return {
            "ok": False,
            "error": status.get("error") or "Ollama unreachable",
            "hint": status.get("hint"),
            "path": path,
        }
    if not use_model:
        return {
            "ok": False,
            "error": "Vision model yoxdur",
            "hint": status.get("hint"),
            "path": path,
            "models": status.get("models"),
        }

    try:
        b64 = _encode_image(path)
    except Exception as e:
        return {"ok": False, "error": str(e), "path": path}

    payload = {
        "model": use_model,
        "prompt": prompt,
        "images": [b64],
        "stream": False,
    }
    base = _ollama_base()
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{base}/api/generate",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=180) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        text = (body.get("response") or "").strip()
        return {
            "ok": bool(text),
            "description": text,
            "model": use_model,
            "path": path,
            "provider": "ollama",
        }
    except Exception as e:
        logger.warning(f"describe_image: {e}")
        return {
            "ok": False,
            "error": str(e),
            "model": use_model,
            "path": path,
            "hint": "Model vision dəstəkləməyə bilər; llava/moondream yoxlayın",
        }
