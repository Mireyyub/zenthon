"""
Image understanding – local visual features + regions + optional VLM multi-pass.
Never fakes VLM success when model is missing.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def _require_pil():
    try:
        return __import__("PIL.Image", fromlist=["Image"])
    except ImportError as e:
        raise RuntimeError("Pillow yoxdur. pip install Pillow") from e


_COLOR_NAMES = [
    ((180, 40, 40), "red"),
    ((40, 140, 40), "green"),
    ((40, 40, 180), "blue"),
    ((200, 180, 40), "yellow"),
    ((200, 100, 30), "orange"),
    ((120, 60, 140), "purple"),
    ((30, 30, 30), "black"),
    ((220, 220, 220), "white"),
    ((140, 90, 50), "brown"),
    ((100, 100, 100), "gray"),
    ((40, 160, 160), "cyan"),
    ((200, 80, 140), "pink"),
]


def _nearest_color_name(rgb: Tuple[int, int, int]) -> str:
    r, g, b = rgb
    best, best_d = "mixed", 1e18
    for (cr, cg, cb), name in _COLOR_NAMES:
        d = (r - cr) ** 2 + (g - cg) ** 2 + (b - cb) ** 2
        if d < best_d:
            best_d, best = d, name
    return best


def local_analyze(path: str) -> Dict[str, Any]:
    """Deterministic visual features without neural nets."""
    Image = _require_pil()
    from PIL import ImageStat, ImageFilter

    p = Path(path).expanduser().resolve()
    if not p.exists():
        return {"ok": False, "error": f"not found: {p}"}

    with Image.open(p) as im:
        im.load()
        rgb = im.convert("RGB")
        w, h = rgb.size
        sample = rgb.resize((max(8, min(64, w)), max(8, min(64, h))))
        stat = ImageStat.Stat(sample)
        mean = [round(x, 1) for x in stat.mean]
        stddev = [round(x, 1) for x in stat.stddev]

        small = rgb.resize((4, 4))
        dom = [tuple(px) for px in small.get_flattened_data()]
        q = rgb.resize((32, 32))
        counts: Dict[Tuple[int, int, int], int] = {}
        for px in q.get_flattened_data():
            key = (px[0] // 32 * 32, px[1] // 32 * 32, px[2] // 32 * 32)
            counts[key] = counts.get(key, 0) + 1
        top_colors = sorted(counts.items(), key=lambda x: -x[1])[:5]

        brightness = sum(mean) / 3.0
        contrast = sum(stddev) / 3.0

        gray = rgb.convert("L").filter(ImageFilter.FIND_EDGES)
        edge_stat = ImageStat.Stat(gray.resize((48, 48)))
        edge_density = round(edge_stat.mean[0] / 255.0, 3)

        aspect = round(w / max(1, h), 3)
        orientation = (
            "landscape" if w > h * 1.1 else ("portrait" if h > w * 1.1 else "square")
        )
        mood = _mood_from_stats(brightness, contrast, mean)

        # quadrant regions
        regions = {}
        for name, box in (
            ("tl", (0, 0, w // 2, h // 2)),
            ("tr", (w // 2, 0, w, h // 2)),
            ("bl", (0, h // 2, w // 2, h)),
            ("br", (w // 2, h // 2, w, h)),
        ):
            crop = rgb.crop(box).resize((16, 16))
            st = ImageStat.Stat(crop)
            m = [round(x, 1) for x in st.mean]
            regions[name] = {
                "mean_rgb": m,
                "brightness": round(sum(m) / 3.0, 1),
                "color": _nearest_color_name((int(m[0]), int(m[1]), int(m[2]))),
            }

        palette = [
            {
                "rgb": list(c),
                "weight": n,
                "name": _nearest_color_name(c),
            }
            for c, n in top_colors
        ]

    return {
        "ok": True,
        "path": str(p),
        "width": w,
        "height": h,
        "orientation": orientation,
        "aspect_ratio": aspect,
        "mean_rgb": mean,
        "stddev_rgb": stddev,
        "brightness": round(brightness, 1),
        "contrast": round(contrast, 1),
        "edge_density": edge_density,
        "dominant_colors": palette,
        "palette_names": [c["name"] for c in palette],
        "regions": regions,
        "sample_grid_rgb": [list(c) for c in dom],
        "mood_heuristic": mood,
        "method": "local_stats+regions",
    }


def _mood_from_stats(brightness: float, contrast: float, mean: List[float]) -> str:
    r, g, b = mean[0], mean[1], mean[2]
    if brightness < 60:
        base = "dark"
    elif brightness > 180:
        base = "bright"
    else:
        base = "balanced"
    if contrast > 70:
        base += "/high-contrast"
    elif contrast < 25:
        base += "/flat"
    if b > r + 20 and b > g + 10:
        base += "/cool"
    elif r > b + 20 and r > g:
        base += "/warm"
    return base


def understand_image(
    path: str,
    *,
    question: Optional[str] = None,
    use_vlm: bool = True,
    inject_facts: bool = False,
    model: Optional[str] = None,
) -> Dict[str, Any]:
    local = local_analyze(path)
    if not local.get("ok"):
        return local

    report: Dict[str, Any] = {
        "ok": True,
        "path": local["path"],
        "local": local,
        "vlm": None,
        "summary": None,
        "answers": {},
    }

    names = local.get("palette_names") or []
    color_txt = ", ".join(names[:3]) if names else "?"
    regs = local.get("regions") or {}
    reg_txt = "; ".join(f"{k}:{v.get('color')}" for k, v in regs.items())
    local_summary = (
        f"Şəkil {local['width']}x{local['height']} ({local['orientation']}); "
        f"mood={local['mood_heuristic']}; edge={local['edge_density']}; "
        f"palette=[{color_txt}]; regions=[{reg_txt}]"
    )
    report["summary"] = local_summary

    if use_vlm:
        from multimodal.vision import describe_image, vision_available

        st = vision_available()
        if st.get("ready"):
            prompts = {
                "caption": "Bir-iki cümlə ilə şəkli təsvir et.",
                "objects": "Şəkildəki əsas obyektləri siyahıla (vergüllə).",
                "scene": "Səhnə növü nədir? (interyer/ext/outdoor/abstract/digər) Qısa cavab.",
                "colors": "Əsas rəngləri qısa siyahıla.",
            }
            if question:
                prompts["user_question"] = question

            vlm_out: Dict[str, Any] = {"model": st.get("vision_model"), "parts": {}}
            for key, pr in prompts.items():
                part = describe_image(path, prompt=pr, model=model or st.get("vision_model"))
                vlm_out["parts"][key] = part
                if part.get("ok") and part.get("description"):
                    report["answers"][key] = part["description"]

            ok_any = any(
                (vlm_out["parts"].get(k) or {}).get("ok") for k in vlm_out["parts"]
            )
            vlm_out["ok"] = ok_any
            if report["answers"].get("caption"):
                report["summary"] = report["answers"]["caption"] + " | " + local_summary
            report["vlm"] = vlm_out
        else:
            report["vlm"] = {
                "ok": False,
                "ready": False,
                "hint": st.get("hint"),
                "error": st.get("error"),
            }

    if inject_facts and report.get("summary"):
        try:
            from knowledge.registry import get_fact_store

            fs = get_fact_store()
            stmt = f"[vision] {Path(path).name}: {report['summary'][:300]}"
            fs.add(stmt, source="vision_understand", confidence=0.7)
            report["fact_injected"] = True
            report["fact_statement"] = stmt
        except Exception as e:
            report["fact_injected"] = False
            report["fact_error"] = str(e)

    return report
