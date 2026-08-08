"""Classic image ops – Pillow soft-dependency, sandbox-safe paths."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def _sandbox_root() -> Path:
    try:
        from core.config import config

        root = Path(config.path.leon_dir) / "sandbox" / "images"
    except Exception:
        root = Path("data/leon/sandbox/images")
    root.mkdir(parents=True, exist_ok=True)
    return root


def _resolve_path(path: str | Path, *, must_exist: bool = True) -> Path:
    p = Path(path).expanduser()
    if not p.is_absolute():
        # relative → under sandbox/images
        p = _sandbox_root() / p
    p = p.resolve()
    sand = _sandbox_root().resolve()
    # allow read outside only for info if absolute and exists; writes always sandbox
    if must_exist and not p.exists():
        raise FileNotFoundError(str(p))
    return p


def _require_pil():
    try:
        from PIL import Image, ImageOps, ImageFilter, ImageDraw, ImageFont  # noqa: F401

        return __import__("PIL.Image", fromlist=["Image"]).Image
    except ImportError as e:
        raise RuntimeError(
            "Pillow yoxdur. Quraşdır: pip install Pillow"
        ) from e


def list_supported() -> Dict[str, Any]:
    try:
        Image = _require_pil()
        formats = sorted(Image.registered_extensions().keys())
        return {"pillow": True, "extensions": formats[:40], "sandbox": str(_sandbox_root())}
    except Exception as e:
        return {"pillow": False, "error": str(e), "sandbox": str(_sandbox_root())}


def image_info(path: str) -> Dict[str, Any]:
    Image = _require_pil()
    p = _resolve_path(path, must_exist=True)
    with Image.open(p) as im:
        im.load()
        mode = im.mode
        size = im.size
        fmt = im.format
        # average color sample
        thumb = im.convert("RGB").resize((8, 8))
        pixels = list(thumb.getdata())
        avg = tuple(sum(c[i] for c in pixels) // max(1, len(pixels)) for i in range(3))
    data = p.read_bytes()
    sha = hashlib.sha256(data).hexdigest()[:16]
    return {
        "path": str(p),
        "format": fmt,
        "mode": mode,
        "width": size[0],
        "height": size[1],
        "bytes": len(data),
        "sha256_16": sha,
        "avg_rgb": avg,
        "ok": True,
    }


def process_image(
    path: str,
    *,
    op: str = "thumbnail",
    width: int = 256,
    height: int = 256,
    out_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    ops: thumbnail | resize | grayscale | blur | invert | rotate90 | rotate180
    Output always under data/leon/sandbox/images/
    """
    Image = _require_pil()
    from PIL import ImageOps, ImageFilter

    src = _resolve_path(path, must_exist=True)
    op = (op or "thumbnail").lower().strip()
    with Image.open(src) as im:
        im.load()
        work = im.convert("RGB") if im.mode not in ("RGB", "RGBA") else im.copy()

        if op == "thumbnail":
            work.thumbnail((max(16, width), max(16, height)))
        elif op == "resize":
            work = work.resize((max(1, width), max(1, height)))
        elif op == "grayscale":
            work = ImageOps.grayscale(work).convert("RGB")
        elif op == "blur":
            work = work.filter(ImageFilter.GaussianBlur(radius=2))
        elif op == "invert":
            work = ImageOps.invert(work.convert("RGB"))
        elif op == "rotate90":
            work = work.rotate(90, expand=True)
        elif op == "rotate180":
            work = work.rotate(180, expand=True)
        else:
            return {"ok": False, "error": f"unknown op: {op}"}

        name = out_name or f"{src.stem}_{op}.png"
        out = _sandbox_root() / Path(name).name
        work.save(out, format="PNG")

    return {
        "ok": True,
        "op": op,
        "source": str(src),
        "output": str(out),
        "info": image_info(str(out)),
    }
