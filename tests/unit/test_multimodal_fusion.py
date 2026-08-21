"""Multimodal fusion smoke."""

from brain.perception.multimodal_fusion import MultimodalFusion
from multimodal.audio import make_tone_wav


def test_fuse_text_only():
    r = MultimodalFusion().fuse(text="salam")
    assert r.get("ok") is True
    assert "text" in (r.get("modalities") or [])
    assert "salam" in (r.get("fused_text") or "")


def test_process_adapts_text_input_for_thinking_brain():
    result = MultimodalFusion().process("salam Leon")
    assert result["summary"] == "salam Leon"
    assert result["modality"] == "text"
    assert result["confidence"] == 0.9


def test_fuse_with_tone(tmp_path):
    p = tmp_path / "t.wav"
    make_tone_wav(seconds=0.05, path=str(p))
    r = MultimodalFusion().fuse(text="dinlə", audio=str(p), use_stt=False)
    assert "audio" in (r.get("modalities") or [])


def test_status():
    s = MultimodalFusion().status()
    assert "supported" in s
