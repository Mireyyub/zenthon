"""
Local image generation – procedural (Pillow), not photoreal diffusion.

For real diffusion users should run external tools; this module never claims AGI art.
"""

from __future__ import annotations

import math
import random
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def _sandbox() -> Path:
    try:
        from core.config import config

        root = Path(config.path.leon_dir) / "sandbox" / "images"
    except Exception:
        root = Path("data/leon/sandbox/images")
    root.mkdir(parents=True, exist_ok=True)
    return root


def _require_pil():
    try:
        from PIL import Image, ImageDraw, ImageFont  # noqa: F401

        return __import__("PIL", fromlist=["Image"]).Image
    except ImportError as e:
        raise RuntimeError("Pillow yoxdur. pip install Pillow") from e


def _palette(seed: int) -> List[Tuple[int, int, int]]:
    rng = random.Random(seed)
    return [
        (rng.randint(30, 220), rng.randint(30, 220), rng.randint(30, 220))
        for _ in range(5)
    ]


def generate_image(
    prompt: str = "leon abstract",
    *,
    width: int = 512,
    height: int = 512,
    style: str = "gradient",
    seed: Optional[int] = None,
    out_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    styles: gradient | noise | shapes | grid | waves

    Procedural only – not Stable Diffusion.
    """
    Image = _require_pil()
    from PIL import ImageDraw

    width = max(32, min(2048, int(width)))
    height = max(32, min(2048, int(height)))
    seed = int(seed if seed is not None else (hash(prompt) & 0xFFFFFFFF))
    rng = random.Random(seed)
    colors = _palette(seed)
    style = (style or "gradient").lower().strip()

    im = Image.new("RGB", (width, height), colors[0])
    draw = ImageDraw.Draw(im)

    if style == "gradient":
        c0, c1 = colors[0], colors[1]
        for y in range(height):
            t = y / max(1, height - 1)
            r = int(c0[0] * (1 - t) + c1[0] * t)
            g = int(c0[1] * (1 - t) + c1[1] * t)
            b = int(c0[2] * (1 - t) + c1[2] * t)
            draw.line([(0, y), (width, y)], fill=(r, g, b))
    elif style == "noise":
        px = im.load()
        for y in range(height):
            for x in range(width):
                px[x, y] = (
                    rng.randint(0, 255),
                    rng.randint(0, 255),
                    rng.randint(0, 255),
                )
    elif style == "shapes":
        draw.rectangle([0, 0, width, height], fill=colors[0])
        for _ in range(12):
            x0, y0 = rng.randint(0, width), rng.randint(0, height)
            x1, y1 = x0 + rng.randint(20, width // 2), y0 + rng.randint(20, height // 2)
            col = colors[rng.randint(0, len(colors) - 1)]
            if rng.random() < 0.5:
                draw.ellipse([x0, y0, x1, y1], fill=col)
            else:
                draw.rectangle([x0, y0, x1, y1], fill=col)
    elif style == "grid":
        draw.rectangle([0, 0, width, height], fill=colors[0])
        step = max(8, min(width, height) // 12)
        for x in range(0, width, step):
            draw.line([(x, 0), (x, height)], fill=colors[1], width=2)
        for y in range(0, height, step):
            draw.line([(0, y), (width, y)], fill=colors[2], width=2)
    elif style == "waves":
        px = im.load()
        for y in range(height):
            for x in range(width):
                v = int(128 + 127 * math.sin(x / 30.0 + seed) * math.cos(y / 40.0))
                px[x, y] = (v, (v + colors[1][1]) % 255, colors[2][2])
    else:
        return {
            "ok": False,
            "error": f"unknown style: {style}",
            "styles": ["gradient", "noise", "shapes", "grid", "waves"],
        }

    # caption strip
    try:
        draw.rectangle([0, height - 28, width, height], fill=(20, 20, 20))
        label = (prompt or "leon")[:60]
        draw.text((8, height - 22), f"Leon · {style} · {label}", fill=(230, 230, 230))
    except Exception:
        pass

    name = out_name or f"gen_{style}_{seed}.png"
    out = _sandbox() / Path(name).name
    im.save(out, format="PNG")
    return {
        "ok": True,
        "path": str(out),
        "style": style,
        "seed": seed,
        "width": width,
        "height": height,
        "prompt": prompt,
        "kind": "procedural",
        "note": "Procedural Pillow generation — not diffusion/VLM art.",
    }


def generate_card(
    title: str,
    subtitle: str = "",
    *,
    width: int = 640,
    height: int = 360,
    out_name: Optional[str] = None,
) -> Dict[str, Any]:
    Image = _require_pil()
    from PIL import ImageDraw

    seed = hash(title) & 0xFFFFFFFF
    colors = _palette(seed)
    im = Image.new("RGB", (width, height), colors[0])
    draw = ImageDraw.Draw(im)
    draw.rectangle([0, height // 3, width, height], fill=colors[1])
    draw.text((24, 40), (title or "Leon")[:80], fill=(255, 255, 255))
    if subtitle:
        draw.text((24, 80), subtitle[:100], fill=(230, 230, 230))
    draw.text((24, height - 32), "Leon multimodal card", fill=(200, 200, 200))
    name = out_name or f"card_{seed}.png"
    out = _sandbox() / Path(name).name
    im.save(out, format="PNG")
    return {"ok": True, "path": str(out), "title": title, "kind": "card"}
