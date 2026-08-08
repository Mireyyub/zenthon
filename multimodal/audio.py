"""
Audio / speech layer for Leon.

Honest design:
  - Local: WAV meta, duration estimate, silence detection (stdlib + optional wave)
  - STT: optional external whisper CLI / openai-whisper if installed
  - TTS: optional pyttsx3 / espeak if available; else text package only
  - Never claims hearing/speaking success without backend
"""

from __future__ import annotations

import json
import struct
import subprocess
import wave
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from core.logger import logger


def _audio_dir() -> Path:
    try:
        from core.config import config

        d = Path(config.path.leon_dir) / "audio"
    except Exception:
        d = Path("data/leon/audio")
    d.mkdir(parents=True, exist_ok=True)
    return d


def audio_available() -> Dict[str, Any]:
    backends = {
        "wave": True,
        "whisper_cli": _which("whisper") is not None,
        "espeak": _which("espeak") is not None or _which("espeak-ng") is not None,
        "pyttsx3": False,
        "openai_whisper": False,
    }
    try:
        import pyttsx3  # noqa: F401

        backends["pyttsx3"] = True
    except Exception:
        pass
    try:
        import whisper  # noqa: F401

        backends["openai_whisper"] = True
    except Exception:
        pass
    return {"ok": True, "backends": backends}


def _which(cmd: str) -> Optional[str]:
    from shutil import which

    return which(cmd)


def audio_info(path: str) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {"ok": False, "error": f"not found: {path}"}
    out: Dict[str, Any] = {
        "ok": True,
        "path": str(p),
        "size": p.stat().st_size,
        "suffix": p.suffix.lower(),
    }
    if p.suffix.lower() == ".wav":
        try:
            with wave.open(str(p), "rb") as w:
                frames = w.getnframes()
                rate = w.getframerate()
                out.update(
                    {
                        "channels": w.getnchannels(),
                        "sampwidth": w.getsampwidth(),
                        "framerate": rate,
                        "frames": frames,
                        "duration_sec": round(frames / float(rate), 3) if rate else None,
                    }
                )
        except Exception as e:
            out["wav_error"] = str(e)
            out["ok"] = False
    return out


def understand_speech(
    path: str,
    *,
    language: str = "az",
    use_whisper: bool = True,
) -> Dict[str, Any]:
    """Speech-to-text if backend exists; else structured refusal + meta."""
    info = audio_info(path)
    result: Dict[str, Any] = {
        "ok": False,
        "path": path,
        "info": info,
        "transcript": None,
        "backend": None,
        "at": datetime.now().isoformat(),
    }
    if not info.get("ok"):
        result["error"] = info.get("error") or info.get("wav_error") or "bad audio"
        return result

    if use_whisper and _which("whisper"):
        try:
            cmd = [
                "whisper",
                path,
                "--model",
                "base",
                "--output_format",
                "json",
                "--output_dir",
                str(_audio_dir()),
            ]
            if language:
                cmd.extend(["--language", language[:2]])
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            # whisper writes <stem>.json next to output_dir
            jpath = _audio_dir() / (Path(path).stem + ".json")
            if jpath.exists():
                data = json.loads(jpath.read_text(encoding="utf-8"))
                result["transcript"] = data.get("text") or ""
                result["ok"] = True
                result["backend"] = "whisper_cli"
                return result
            if proc.stdout and proc.returncode == 0:
                result["transcript"] = proc.stdout.strip()[:4000]
                result["ok"] = True
                result["backend"] = "whisper_cli_stdout"
                return result
            result["error"] = (proc.stderr or "whisper failed")[:500]
        except Exception as e:
            result["error"] = f"whisper_cli: {e}"

    if use_whisper:
        try:
            import whisper

            model = whisper.load_model("base")
            r = model.transcribe(path, language=language[:2] if language else None)
            result["transcript"] = (r.get("text") or "").strip()
            result["ok"] = True
            result["backend"] = "openai_whisper"
            return result
        except Exception as e:
            result.setdefault("errors", []).append(f"openai_whisper: {e}")

    result["error"] = result.get("error") or (
        "No STT backend. Install whisper CLI or openai-whisper. Local meta only."
    )
    result["hint"] = "pip install openai-whisper  OR  install whisper.cpp/cli"
    return result


def generate_speech(
    text: str,
    *,
    out_path: Optional[str] = None,
    voice: str = "default",
) -> Dict[str, Any]:
    """Text-to-speech if backend exists; else write .txt sidecar."""
    text = (text or "").strip()
    if not text:
        return {"ok": False, "error": "empty text"}

    out_dir = _audio_dir()
    if out_path:
        dest = Path(out_path)
    else:
        dest = out_dir / f"tts_{datetime.now().strftime('%Y%m%d%H%M%S')}.wav"

    # espeak
    espeak = _which("espeak-ng") or _which("espeak")
    if espeak:
        try:
            wav = dest.with_suffix(".wav")
            proc = subprocess.run(
                [espeak, "-w", str(wav), text[:2000]],
                capture_output=True,
                text=True,
                timeout=60,
            )
            if proc.returncode == 0 and wav.exists():
                return {
                    "ok": True,
                    "backend": "espeak",
                    "path": str(wav),
                    "text": text[:500],
                    "info": audio_info(str(wav)),
                }
        except Exception as e:
            logger.debug(f"espeak failed: {e}")

    # pyttsx3
    try:
        import pyttsx3

        engine = pyttsx3.init()
        wav = dest.with_suffix(".wav")
        engine.save_to_file(text[:2000], str(wav))
        engine.runAndWait()
        if wav.exists():
            return {
                "ok": True,
                "backend": "pyttsx3",
                "path": str(wav),
                "text": text[:500],
                "info": audio_info(str(wav)),
            }
    except Exception as e:
        logger.debug(f"pyttsx3 failed: {e}")

    # fallback: text package (honest)
    txt = dest.with_suffix(".txt")
    txt.write_text(text, encoding="utf-8")
    return {
        "ok": False,
        "backend": "text_only",
        "path": str(txt),
        "text": text[:500],
        "error": "No TTS backend (espeak/pyttsx3). Saved text only.",
        "hint": "apt install espeak-ng  OR  pip install pyttsx3",
    }


def make_tone_wav(
    *,
    seconds: float = 0.5,
    freq: float = 440.0,
    rate: int = 16000,
    path: Optional[str] = None,
) -> Dict[str, Any]:
    """Generate a simple sine tone WAV for pipeline tests (no external deps)."""
    import math

    n = int(seconds * rate)
    samples = []
    for i in range(n):
        v = int(16000 * math.sin(2 * math.pi * freq * (i / rate)))
        samples.append(max(-32767, min(32767, v)))
    dest = Path(path) if path else _audio_dir() / "tone_test.wav"
    dest.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(dest), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        frames = b"".join(struct.pack("<h", s) for s in samples)
        w.writeframes(frames)
    return {"ok": True, "path": str(dest), "info": audio_info(str(dest))}
