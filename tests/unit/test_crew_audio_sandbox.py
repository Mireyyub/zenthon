"""Crew modes, audio meta, sandbox python."""

from agents.crew import Crew, run_crew
from multimodal.audio import audio_available, make_tone_wav, audio_info
from security.sandbox import Sandbox


def test_crew_sequential_empty():
    c = Crew(name="t")
    r = c.run("goal", mode="sequential")
    assert r.mode == "sequential"
    assert r.success is False or r.outputs == []


def test_run_crew_dict():
    # may fail agents if heavy; structure only
    out = run_crew("echo test", [{"description": "noop-ish", "agent": "react"}], mode="sequential")
    assert "mode" in out
    assert "outputs" in out


def test_audio_available():
    a = audio_available()
    assert a.get("ok") is True
    assert "backends" in a


def test_tone_wav(tmp_path):
    p = tmp_path / "t.wav"
    r = make_tone_wav(seconds=0.1, path=str(p))
    assert r.get("ok") is True
    info = audio_info(str(p))
    assert info.get("ok") is True
    assert info.get("duration_sec", 0) > 0


def test_sandbox_python_ok():
    sb = Sandbox(timeout_seconds=5)
    r = sb.run_python("print(1+1)")
    assert r.get("ok") is True
    assert "2" in (r.get("stdout") or "")


def test_sandbox_forbidden():
    sb = Sandbox(timeout_seconds=5)
    try:
        sb.run_python("import os; os.system('echo x')")
        assert False, "should raise"
    except Exception as e:
        assert "Forbidden" in str(e) or "Security" in type(e).__name__
