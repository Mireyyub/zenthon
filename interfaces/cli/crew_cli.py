"""CLI for multi-agent crew and audio."""

from __future__ import annotations

import json
from typing import Any


def run_crew_cmd(args: Any) -> None:
    from agents.crew import Crew, default_research_crew, multimodal_crew, run_crew

    mode = getattr(args, "mode", "sequential") or "sequential"
    goal = getattr(args, "goal", None) or getattr(args, "query", None) or ""
    if getattr(args, "research", False):
        crew = default_research_crew(goal)
        result = crew.run(goal, mode=mode)
        out = {
            "success": result.success,
            "mode": result.mode,
            "final": result.final,
            "outputs": result.outputs,
        }
    elif getattr(args, "image", None):
        crew = multimodal_crew(goal, image_path=args.image)
        result = crew.run(goal, mode=mode)
        out = {
            "success": result.success,
            "mode": result.mode,
            "final": result.final,
            "outputs": result.outputs,
        }
    else:
        agents = [
            a.strip()
            for a in (getattr(args, "agents", "react,coding") or "react,coding").split(",")
            if a.strip()
        ]
        tasks = [{"description": goal, "agent": a} for a in agents]
        out = run_crew(goal, tasks, mode=mode)
    print(json.dumps(out, ensure_ascii=False, indent=2, default=str))


def run_audio_cmd(args: Any) -> None:
    from multimodal.audio import (
        audio_available,
        audio_info,
        understand_speech,
        generate_speech,
        make_tone_wav,
    )

    cmd = getattr(args, "audio_cmd", None)
    if cmd == "status" or cmd is None:
        print(json.dumps(audio_available(), ensure_ascii=False, indent=2))
        return
    if cmd == "info":
        print(json.dumps(audio_info(args.path), ensure_ascii=False, indent=2, default=str))
        return
    if cmd == "stt":
        print(json.dumps(understand_speech(args.path), ensure_ascii=False, indent=2, default=str))
        return
    if cmd == "tts":
        print(
            json.dumps(
                generate_speech(args.text or "", out_path=getattr(args, "out", None)),
                ensure_ascii=False,
                indent=2,
                default=str,
            )
        )
        return
    if cmd == "tone":
        print(json.dumps(make_tone_wav(), ensure_ascii=False, indent=2, default=str))
        return
    print("audio status|info|stt|tts|tone")
