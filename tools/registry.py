"""Tool Registry – allowlist-aware (+ audio + understand)."""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field

from core.logger import logger


@dataclass
class Tool:
    name: str
    description: str
    func: Callable
    parameters: Dict[str, str] = field(default_factory=dict)
    production: bool = True


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    def register(
        self,
        name: str,
        func: Callable,
        description: str = "",
        parameters: Optional[Dict[str, str]] = None,
        production: bool = True,
    ) -> None:
        self._tools[name] = Tool(
            name=name,
            description=description,
            func=func,
            parameters=parameters or {},
            production=production,
        )
        logger.info(f"ToolRegistry: registered '{name}'")

    def get(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)

    def call(self, name: str, **kwargs) -> Any:
        tool = self._tools.get(name)
        if not tool:
            raise KeyError(f"Tool not found: {name}")
        return tool.func(**kwargs)

    def dispatch(self, name: str, arg: str = "", *, enforce_security: bool = True) -> Any:
        name = (name or "").strip()
        arg = (arg or "").strip()
        if enforce_security:
            try:
                from security.gate import gate_tool

                gate_tool(name, user="agent", arg=arg)
            except Exception as e:
                from core.exceptions import SecurityError

                if isinstance(e, SecurityError) or "SecurityError" in type(e).__name__:
                    raise
                if not isinstance(e, (ImportError, ModuleNotFoundError)):
                    raise
        tool = self._tools.get(name)
        if not tool:
            raise KeyError(f"Tool not found: {name}")
        params = list(tool.parameters.keys())
        if not params:
            return tool.func()
        key = params[0]
        if name == "write_file" and "||" in arg:
            path, content = arg.split("||", 1)
            return tool.func(path=path.strip(), content=content)
        if name == "write_file":
            return tool.func(path=arg, content="")
        if key in ("text", "expression", "code", "content", "prompt"):
            return tool.func(**{key: arg})
        if key == "path":
            return tool.func(path=arg or ".")
        if name == "image_process" and "||" in arg:
            path, op = arg.split("||", 1)
            return tool.func(path=path.strip(), op=op.strip())
        return tool.func(**{key: arg})

    def list_tools(self, production_only: bool = False) -> List[Dict[str, str]]:
        out = []
        for t in self._tools.values():
            if production_only and not t.production:
                continue
            out.append(
                {
                    "name": t.name,
                    "description": t.description,
                    "production": str(t.production),
                }
            )
        return out


tool_registry = ToolRegistry()


def _echo(text: str = "") -> str:
    return text


def _get_time() -> str:
    from datetime import datetime

    return datetime.now().isoformat()


def _register_builtins():
    tool_registry.register("echo", _echo, "Verilən mətni qaytarır", {"text": "str"})
    tool_registry.register("get_time", _get_time, "Cari vaxtı qaytarır")
    try:
        from tools.safe_fs import list_dir, read_file, write_file, calc, run_python

        tool_registry.register("list_dir", list_dir, "Sandbox qovluğunu siyahıla", {"path": "str"})
        tool_registry.register("read_file", read_file, "Sandbox faylını oxu", {"path": "str"})
        tool_registry.register(
            "write_file",
            write_file,
            "Sandbox-a yaz (path||content)",
            {"path": "str", "content": "str"},
        )
        tool_registry.register("calc", calc, "Təhlükəsiz riyazi ifadə", {"expression": "str"})
        tool_registry.register("run_python", run_python, "Məhdud Python sandbox", {"code": "str"})
    except Exception as e:
        logger.warning(f"safe_fs tools not loaded: {e}")

    try:
        from native_core import get_native_core, health_report

        native_core = get_native_core()
        tool_registry.register("native_core_status", health_report, "Native core acceleration status")
        tool_registry.register(
            "normalize_text",
            lambda text="": native_core.normalize_text(text).as_dict(),
            "Text normalization with optional native acceleration",
            {"text": "str"},
        )
        tool_registry.register(
            "text_fingerprint",
            lambda text="": native_core.fingerprint(text).as_dict(),
            "SHA-256 fingerprint with optional native acceleration",
            {"text": "str"},
        )
        tool_registry.register(
            "text_metrics",
            lambda text="": native_core.token_metrics(text).as_dict(),
            "Token metrics with optional native acceleration",
            {"text": "str"},
        )
    except Exception as e:
        logger.debug(f"native-core tools not loaded: {e}")

    try:
        from multimodal.image_ops import image_info, process_image
        from multimodal.generate import generate_image
        from multimodal.vision import describe_image
        from multimodal.understand import understand_image

        def _img_info(path: str = "") -> Any:
            return image_info(path)

        def _img_process(path: str = "", op: str = "thumbnail") -> Any:
            return process_image(path, op=op or "thumbnail")

        def _img_gen(prompt: str = "leon") -> Any:
            return generate_image(prompt=prompt or "leon", style="gradient")

        def _img_desc(path: str = "") -> Any:
            return describe_image(path)

        def _img_understand(path: str = "") -> Any:
            return understand_image(path, use_vlm=True, inject_facts=False)

        tool_registry.register("image_info", _img_info, "Şəkil meta", {"path": "str"})
        tool_registry.register(
            "image_process", _img_process, "path||op (thumbnail|grayscale|...)", {"path": "str", "op": "str"}
        )
        tool_registry.register(
            "image_generate", _img_gen, "Procedural şəkil generasiya", {"prompt": "str"}, production=False
        )
        tool_registry.register(
            "image_describe", _img_desc, "Ollama VLM təsvir", {"path": "str"}, production=False
        )
        tool_registry.register(
            "image_understand", _img_understand, "Local+VLM anlama", {"path": "str"}, production=False
        )
    except Exception as e:
        logger.debug(f"image tools not loaded: {e}")

    try:
        from multimodal.audio import (
            audio_info,
            audio_available,
            understand_speech,
            generate_speech,
            make_tone_wav,
        )

        tool_registry.register("audio_status", lambda: audio_available(), "Audio backend status")
        tool_registry.register("audio_info", audio_info, "WAV/audio meta", {"path": "str"})
        tool_registry.register(
            "speech_to_text", understand_speech, "STT (whisper if installed)", {"path": "str"}, production=False
        )
        tool_registry.register(
            "text_to_speech", generate_speech, "TTS (espeak/pyttsx3 if installed)", {"text": "str"}, production=False
        )
        tool_registry.register(
            "tone_wav", lambda: make_tone_wav(), "Test sine WAV", production=False
        )
    except Exception as e:
        logger.debug(f"audio tools not loaded: {e}")

    try:
        from agents.crew import run_crew

        def _crew(prompt: str = "") -> Any:
            return run_crew(
                prompt or "analyze",
                [
                    {"description": prompt or "analyze", "agent": "react"},
                    {"description": "Summarize prior", "agent": "coding"},
                ],
                mode="sequential",
            )

        tool_registry.register(
            "crew_run", _crew, "Mini multi-agent crew", {"prompt": "str"}, production=False
        )
    except Exception as e:
        logger.debug(f"crew tool not loaded: {e}")


_register_builtins()
