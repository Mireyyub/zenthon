"""
ReAct Agent – Thought → Action → Observation (Faza 5 production).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import re

from agents.base import BaseAgent, AgentResult
from core.logger import logger


class ReActAgent(BaseAgent):
    MAX_STEPS = 6
    PRODUCTION = True

    def __init__(self, name: str = "ReActAgent", description: str = "ReAct tool-calling agent"):
        super().__init__(name=name, description=description)

    def run(self, task: str, context: Optional[Dict[str, Any]] = None) -> AgentResult:
        context = context or {}
        max_steps = int(context.get("max_steps", self.MAX_STEPS))

        try:
            from tools.registry import tool_registry
            from brain.llm.client import get_llm_client
        except Exception as e:
            return AgentResult(success=False, error=f"Deps missing: {e}")

        tools = tool_registry.list_tools(production_only=True)
        tool_desc = "\n".join(f"- {t['name']}: {t['description']}" for t in tools) or "(no tools)"

        client = get_llm_client()
        scratch: List[str] = []
        observations: List[str] = []

        system = (
            "Sən ReAct agentisən. Hər addımda YALNIZ bu formatdan birini yaz:\n"
            "Thought: <düşüncə>\n"
            "Action: <tool_name> | <arg>\n"
            "və ya\n"
            "Final: <yekun cavab>\n\n"
            f"Mövcud alətlər:\n{tool_desc}\n"
            "write_file üçün arg: path||content"
        )

        # Heuristic tool path without LLM when possible
        low = task.lower()
        if any(k in low for k in ("saat", "vaxt", "time")):
            try:
                obs = tool_registry.dispatch("get_time", "")
                return AgentResult(
                    success=True,
                    output=str(obs),
                    metadata={"steps": 1, "method": "react-heuristic", "tool": "get_time"},
                )
            except Exception:
                pass

        for step in range(1, max_steps + 1):
            prompt_parts = [f"Tapşırıq: {task}"]
            if observations:
                prompt_parts.append("Əvvəlki müşahidələr:\n" + "\n".join(observations[-4:]))
            prompt_parts.append(f"Addım {step}. Thought/Action və ya Final yaz.")
            prompt = "\n\n".join(prompt_parts)

            if client.is_available:
                raw = client.complete(prompt, system=system, temperature=0.2, max_tokens=400) or ""
            else:
                # offline fallback: try calc if expression-like
                if re.search(r"[\d\+\-\*/]+", task) and any(c in task for c in "+-*/"):
                    expr = re.sub(r"[^0-9\+\-\*/\.\(\) ]", "", task)
                    try:
                        obs = tool_registry.dispatch("calc", expr.strip())
                        return AgentResult(
                            success=True,
                            output=str(obs),
                            metadata={"steps": 1, "method": "react-offline-calc"},
                        )
                    except Exception:
                        pass
                raw = f"Final: {task} (LLM offline – tool nəticəsi yoxdur)."

            scratch.append(raw.strip())
            logger.info(f"ReAct step {step}: {raw[:120]}")

            final_m = re.search(r"Final:\s*(.+)", raw, re.I | re.S)
            if final_m:
                return AgentResult(
                    success=True,
                    output=final_m.group(1).strip(),
                    metadata={"steps": step, "trace": scratch, "method": "react"},
                )

            action_m = re.search(r"Action:\s*([\w_]+)\s*\|\s*(.*)", raw, re.I)
            if action_m:
                tool_name = action_m.group(1).strip()
                arg = action_m.group(2).strip()
                try:
                    obs = tool_registry.dispatch(tool_name, arg)
                    observations.append(f"Observation[{tool_name}]: {str(obs)[:400]}")
                except Exception as e:
                    observations.append(f"Observation[{tool_name}]: ERROR {e}")
            else:
                observations.append("Observation: format tanınmadı.")

        return AgentResult(
            success=True,
            output=observations[-1] if observations else "Max steps reached",
            metadata={"steps": max_steps, "trace": scratch, "method": "react", "truncated": True},
        )
