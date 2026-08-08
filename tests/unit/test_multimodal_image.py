"""Multimodal image ops + procedural generate (no Ollama required)."""

from __future__ import annotations

import pytest


@pytest.fixture()
def img_env(tmp_path, monkeypatch):
    leon = tmp_path / "leon"
    (leon / "sandbox" / "images").mkdir(parents=True)
    monkeypatch.setenv("LEON_DATA_DIR", str(tmp_path))
    import core.config as cfg

    cfg.config = cfg.load_config()
    return tmp_path


def test_generate_and_info(img_env):
    pytest.importorskip("PIL")
    from multimodal.generate import generate_image
    from multimodal.image_ops import image_info, process_image

    gen = generate_image("test leon", style="shapes", width=128, height=128, seed=42)
    assert gen.get("ok")
    path = gen["path"]
    info = image_info(path)
    assert info.get("width") == 128
    out = process_image(path, op="grayscale", width=64, height=64)
    assert out.get("ok")
    assert out.get("output")


def test_vision_status_soft():
    from multimodal.vision import vision_available

    st = vision_available()
    assert "ready" in st
    assert "reachable" in st
