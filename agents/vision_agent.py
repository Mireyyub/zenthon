"""
Vision Agent – image info / process / describe / generate.

Experimental: describe needs Ollama vision model; generate is procedural.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Optional

from agents.base import BaseAgent, AgentResult


class VisionAgent(BaseAgent):
    PRODUCTION = False

    def __init__(self, name: str = "VisionAgent", description: str = "Image ops + optional VLM"):
        super().__init__(name=name, description=description)

    def run(self, task: str, context: Optional[Dict[str, Any]] = None) -> AgentResult:
        ctx = context or {}
        task_l = (task or "").lower().strip()
        path = ctx.get("path") or ctx.get("image") or self._extract_path(task)

        try:
            if any(k in task_l for k in ("generate", "generasiya", "yarat", "draw", "rəsm")):
                return self._generate(task, ctx)
            if any(k in task_l for k in ("describe", "təsvir", "nə görünür", "what is")):
                return self._describe(path, task, ctx)
            if any(k in task_l for k in ("process", "resize", "thumbnail", "grayscale", "blur")):
                return self._process(path, task_l, ctx)
            if path:
                return self._info(path)
            # status
            from multimodal.vision import vision_available
            from multimodal.image_ops import list_supported

            return AgentResult(
                success=True,
                output={
                    "vision": vision_available(),
                    "pillow": list_supported(),
                    "usage": {
                        "info": "path in context or task",
                        "describe": "describe <path>",
                        "generate": "generate gradient abstract",
                        "process": "thumbnail|grayscale path",
                    },
                },
                metadata={"experimental": True},
            )
        except Exception as e:
            return AgentResult(
                success=False,
                error=str(e),
                metadata={"experimental": True, "task": (task or "")[:120]},
            )

    def _extract_path(self, task: str) -> Optional[str]:
        if not task:
            return None
        m = re.search(r"([\w./\\-]+\.(?:png|jpg|jpeg|gif|webp|bmp))", task, re.I)
        return m.group(1) if m else None

    def _info(self, path: str) -> AgentResult:
        from multimodal.image_ops import image_info

        info = image_info(path)
        return AgentResult(success=True, output=info, metadata={"op": "info"})

    def _process(self, path: Optional[str], task_l: str, ctx: Dict) -> AgentResult:
        if not path:
            return AgentResult(success=False, error="path lazımdır (context.path və ya task-da fayl)")
        op = ctx.get("op") or "thumbnail"
        for cand in ("thumbnail", "resize", "grayscale", "blur", "invert", "rotate90", "rotate180"):
            if cand in task_l:
                op = cand
                break
        from multimodal.image_ops import process_image

        out = process_image(
            path,
            op=op,
            width=int(ctx.get("width") or 256),
            height=int(ctx.get("height") or 256),
        )
        return AgentResult(success=bool(out.get("ok")), output=out, error=out.get("error"), metadata={"op": op})

    def _describe(self, path: Optional[str], task: str, ctx: Dict) -> AgentResult:
        if not path:
            return AgentResult(
                success=False,
                error="describe üçün şəkil path lazımdır",
                metadata={"hint": "context={'path': 'img.png'} və ya task-da fayl adı"},
            )
        from multimodal.vision import describe_image

        prompt = ctx.get("prompt") or task or "Bu şəkli təsvir et."
        out = describe_image(path, prompt=prompt, model=ctx.get("model"))
        return AgentResult(
            success=bool(out.get("ok")),
            output=out,
            error=out.get("error"),
            metadata={"op": "describe", "experimental": True},
        )

    def _generate(self, task: str, ctx: Dict) -> AgentResult:
        from multimodal.generate import generate_image, generate_card

        style = ctx.get("style") or "gradient"
        for s in ("gradient", "noise", "shapes", "grid", "waves"):
            if s in task.lower():
                style = s
                break
        if "card" in task.lower() or ctx.get("card"):
            out = generate_card(
                ctx.get("title") or task[:60],
                subtitle=ctx.get("subtitle") or "Leon",
                width=int(ctx.get("width") or 640),
                height=int(ctx.get("height") or 360),
            )
        else:
            out = generate_image(
                prompt=task,
                width=int(ctx.get("width") or 512),
                height=int(ctx.get("height") or 512),
                style=style,
                seed=ctx.get("seed"),
            )
        return AgentResult(
            success=bool(out.get("ok")),
            output=out,
            error=out.get("error"),
            metadata={"op": "generate", "kind": out.get("kind"), "experimental": True},
        )
