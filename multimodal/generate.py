"""
Local image generation – procedural (Pillow), not photoreal diffusion.
Supports keyword scene composition from prompt text.
"""

from __future__ import annotations

import math
import random
import re
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


def _palette(seed: int, theme: str = "default") -> List[Tuple[int, int, int]]:
    rng = random.Random(seed)
    themes = {
        "night": [(10, 15, 40), (30, 40, 80), (200, 200, 100), (80, 90, 120), (15, 20, 50)],
        "sunset": [(40, 20, 60), (220, 100, 40), (255, 160, 60), (80, 40, 90), (30, 20, 40)],
        "ocean": [(10, 40, 80), (20, 90, 140), (40, 160, 180), (200, 220, 230), (5, 30, 60)],
        "forest": [(20, 40, 15), (40, 90, 30), (80, 140, 50), (120, 100, 40), (30, 50, 25)],
        "default": [
            (rng.randint(30, 220), rng.randint(30, 220), rng.randint(30, 220))
            for _ in range(5)
        ],
    }
    if theme not in themes:
        theme = "default"
    if theme == "default":
        return themes["default"]
    base = list(themes[theme])
    rng.shuffle(base)
    return base


def _detect_theme(prompt: str) -> str:
    p = (prompt or "").lower()
    if any(k in p for k in ("night", "gecə", "ay", "moon", "ulduz")):
        return "night"
    if any(k in p for k in ("sunset", "gün bat", "axşam", "orange")):
        return "sunset"
    if any(k in p for k in ("ocean", "dəniz", "sea", "beach", "wave")):
        return "ocean"
    if any(k in p for k in ("forest", "meşə", "tree", "ağac", "green")):
        return "forest"
    return "default"


def _detect_style(prompt: str, style: str) -> str:
    if style and style != "auto":
        return style
    p = (prompt or "").lower()
    if any(k in p for k in ("scene", "səhnə", "landscape", "mənzərə", "house", "ev", "sun", "günəş")):
        return "scene"
    if any(k in p for k in ("wave", "dalğa")):
        return "waves"
    if any(k in p for k in ("grid", "tor")):
        return "grid"
    if any(k in p for k in ("noise", "noise", "static")):
        return "noise"
    if any(k in p for k in ("shape", "geo", "abstract")):
        return "shapes"
    return "gradient"


def _draw_scene(draw, width: int, height: int, prompt: str, colors, rng: random.Random) -> List[str]:
    """Compose simple symbolic scene from keywords."""
    p = (prompt or "").lower()
    tags: List[str] = []

    # sky
    draw.rectangle([0, 0, width, int(height * 0.55)], fill=colors[0])
    tags.append("sky")
    # ground
    draw.rectangle([0, int(height * 0.55), width, height], fill=colors[1])
    tags.append("ground")

    if any(k in p for k in ("sun", "günəş", "gün")):
        r = min(width, height) // 10
        cx, cy = int(width * 0.8), int(height * 0.2)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 220, 80))
        tags.append("sun")
    if any(k in p for k in ("moon", "ay")):
        r = min(width, height) // 12
        cx, cy = int(width * 0.75), int(height * 0.18)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(230, 230, 240))
        tags.append("moon")
    if any(k in p for k in ("star", "ulduz")):
        for _ in range(18):
            x, y = rng.randint(0, width), rng.randint(0, int(height * 0.5))
            draw.point((x, y), fill=(255, 255, 255))
            draw.ellipse([x, y, x + 2, y + 2], fill=(255, 255, 200))
        tags.append("stars")
    if any(k in p for k in ("tree", "ağac", "forest", "meşə")):
        for i in range(3):
            tx = int(width * (0.2 + i * 0.25))
            base_y = int(height * 0.7)
            draw.rectangle([tx - 4, base_y - 40, tx + 4, base_y], fill=(90, 60, 30))
            draw.ellipse([tx - 22, base_y - 80, tx + 22, base_y - 20], fill=colors[2])
        tags.append("trees")
    if any(k in p for k in ("house", "ev", "building", "bina")):
        hx = int(width * 0.35)
        hy = int(height * 0.55)
        draw.rectangle([hx, hy, hx + 70, hy + 55], fill=(180, 140, 100))
        draw.polygon([(hx - 8, hy), (hx + 35, hy - 30), (hx + 78, hy)], fill=(140, 60, 50))
        draw.rectangle([hx + 28, hy + 25, hx + 42, hy + 55], fill=(60, 40, 20))
        tags.append("house")
    if any(k in p for k in ("sea", "ocean", "dəniz", "water", "su")):
        draw.rectangle([0, int(height * 0.6), width, height], fill=colors[2])
        for i in range(6):
            y = int(height * 0.65) + i * 10
            draw.arc([20, y, width - 20, y + 20], 0, 180, fill=(255, 255, 255))
        tags.append("water")
    if any(k in p for k in ("cloud", "bulud")):
        for i in range(3):
            cx = int(width * (0.15 + i * 0.3))
            cy = int(height * 0.2)
            draw.ellipse([cx, cy, cx + 50, cy + 25], fill=(240, 240, 245))
            draw.ellipse([cx + 20, cy - 10, cx + 70, cy + 20], fill=(250, 250, 255))
        tags.append("clouds")
    if any(k in p for k in ("mountain", "dağ")):
        draw.polygon(
            [(0, int(height * 0.55)), (width // 3, int(height * 0.25)), (width // 2, int(height * 0.55))],
            fill=colors[3],
        )
        draw.polygon(
            [(width // 3, int(height * 0.55)), (int(width * 0.7), int(height * 0.2)), (width, int(height * 0.55))],
            fill=colors[4] if len(colors) > 4 else colors[1],
        )
        tags.append("mountains")

    if not any(t in tags for t in ("sun", "moon", "trees", "house", "water", "clouds", "mountains", "stars")):
        # abstract accent
        for _ in range(8):
            x0, y0 = rng.randint(0, width), rng.randint(0, height)
            draw.ellipse([x0, y0, x0 + rng.randint(10, 40), y0 + rng.randint(10, 40)], fill=colors[2])
        tags.append("abstract_accents")
    return tags


def generate_image(
    prompt: str = "leon abstract",
    *,
    width: int = 512,
    height: int = 512,
    style: str = "auto",
    seed: Optional[int] = None,
    out_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    styles: auto | gradient | noise | shapes | grid | waves | scene
    """
    Image = _require_pil()
    from PIL import ImageDraw

    width = max(32, min(2048, int(width)))
    height = max(32, min(2048, int(height)))
    seed = int(seed if seed is not None else (hash(prompt) & 0xFFFFFFFF))
    rng = random.Random(seed)
    theme = _detect_theme(prompt)
    colors = _palette(seed, theme)
    style = _detect_style(prompt, style or "auto")

    im = Image.new("RGB", (width, height), colors[0])
    draw = ImageDraw.Draw(im)
    scene_tags: List[str] = []

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
                px[x, y] = (rng.randint(0, 255), rng.randint(0, 255), rng.randint(0, 255))
    elif style == "shapes":
        draw.rectangle([0, 0, width, height], fill=colors[0])
        for _ in range(14):
            x0, y0 = rng.randint(0, width), rng.randint(0, height)
            x1 = x0 + rng.randint(20, width // 2)
            y1 = y0 + rng.randint(20, height // 2)
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
    elif style == "scene":
        scene_tags = _draw_scene(draw, width, height, prompt, colors, rng)
    else:
        return {
            "ok": False,
            "error": f"unknown style: {style}",
            "styles": ["auto", "gradient", "noise", "shapes", "grid", "waves", "scene"],
        }

    try:
        draw.rectangle([0, height - 28, width, height], fill=(20, 20, 20))
        label = (prompt or "leon")[:55]
        draw.text((8, height - 22), f"Leon · {style}/{theme} · {label}", fill=(230, 230, 230))
    except Exception:
        pass

    name = out_name or f"gen_{style}_{seed}.png"
    out = _sandbox() / Path(name).name
    im.save(out, format="PNG")
    return {
        "ok": True,
        "path": str(out),
        "style": style,
        "theme": theme,
        "seed": seed,
        "width": width,
        "height": height,
        "prompt": prompt,
        "scene_tags": scene_tags,
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
    colors = _palette(seed, _detect_theme(title + " " + subtitle))
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
