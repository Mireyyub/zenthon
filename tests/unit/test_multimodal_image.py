"""Multimodal understand + scene generate + regions."""

from __future__ import annotations

import pytest


@pytest.fixture()
def img_env(tmp_path, monkeypatch):
    leon = tmp_path / "leon"
    (leon / "sandbox" / "images").mkdir(parents=True)
    (leon / "facts").mkdir(parents=True)
    monkeypatch.setenv("LEON_DATA_DIR", str(tmp_path))
    import core.config as cfg

    cfg.config = cfg.load_config()
    import knowledge.registry as reg

    reg._fact_store = None
    reg._graph = None
    return tmp_path


def test_scene_generate_and_understand(img_env):
    pytest.importorskip("PIL")
    from multimodal.generate import generate_image
    from multimodal.understand import understand_image, local_analyze

    gen = generate_image(
        "gecə ay ulduz meşə", style="scene", width=160, height=120, seed=7
    )
    assert gen.get("ok")
    path = gen["path"]
    loc = local_analyze(path)
    assert loc.get("ok")
    assert loc.get("width") == 160
    assert "regions" in loc
    assert set(loc["regions"].keys()) >= {"tl", "tr", "bl", "br"}
    assert loc.get("palette_names")
    und = understand_image(path, use_vlm=False, inject_facts=True)
    assert und.get("ok")
    assert und.get("summary")
    assert und.get("local", {}).get("regions")


def test_vision_status_soft():
    from multimodal.vision import vision_available

    st = vision_available()
    assert "ready" in st


def test_local_palette_names(img_env):
    pytest.importorskip("PIL")
    from PIL import Image
    from multimodal.understand import local_analyze

    p = img_env / "leon" / "sandbox" / "images" / "red.png"
    p.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (64, 64), (200, 30, 30)).save(p)
    loc = local_analyze(str(p))
    assert loc.get("ok")
    assert "red" in (loc.get("palette_names") or []) or loc["regions"]["tl"]["color"] == "red"
