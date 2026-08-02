"""
ReAct Agent – Thought → Action → Observation döngüsü.

İlham: Yao et al. 2022 (ReAct). Tool registry ilə işləyir.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import re

from agents.base import BaseAgent, AgentResult
from core.logger import logger


class ReActAgent(BaseAgent):
    """Tool-using ReAct agent."""

    MAX_STEPS = 6

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

        tools = tool_registry.list_tools()
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
            f"Mövcud alətlər:\n{tool_desc}"
        )

        for step in range(1, max_steps + 1):
            prompt_parts = [f"Tapşırıq: {task}"]
            if observations:
                prompt_parts.append("Əvvəlki müşahidələr:\n" + "\n".join(observations[-4:]))
            prompt_parts.append(f"Addım {step}. Thought/Action və ya Final yaz.")
            prompt = "\n\n".join(prompt_parts)

            if client.is_available:
                raw = client.complete(prompt, system=system, temperature=0.3, max_tokens=400) or ""
            else:
                # Fallback without LLM: birbaşa final
                raw = f"Final: {task} üçün sadə cavab (LLM yoxdur)."

            scratch.append(raw.strip())
            logger.info(f"ReAct step {step}: {raw[:120]}")

            # Final?
            final_m = re.search(r"Final:\s*(.+)", raw, re.I | re.S)
            if final_m:
                return AgentResult(
                    success=True,
                    output=final_m.group(1).strip(),
                    metadata={"steps": step, "trace": scratch, "method": "react"},
                )

            # Action?
            action_m = re.search(r"Action:\s*(\w+)\s*\|\s*(.+)", raw, re.I)
            if action_m:
                tool_name = action_m.group(1).strip()
                arg = action_m.group(2).strip()
                try:
                    # Əksər built-in tool-lar sadə imza ilə
                    if tool_name == "echo":
                        obs = tool_registry.call("echo", text=arg)
                    elif tool_name == "get_time":
                        obs = tool_registry.call("get_time")
                    elif tool_name == "list_dir":
                        obs = tool_registry.call("list_dir", path=arg or ".")
                    elif tool_name == "read_file":
                        obs = tool_registry.call("read_file", path=arg)
                    else:
                        obs = tool_registry.call(tool_name)
                    observations.append(f"Observation[{tool_name}]: {str(obs)[:300]}")
                except Exception as e:
                    observations.append(f"Observation[{tool_name}]: ERROR {e}")
            else:
                observations.append("Observation: format tanınmadı, davam edirəm.")

        return AgentResult(
            success=True,
            output=observations[-1] if observations else "Max steps reached",
            metadata={"steps": max_steps, "trace": scratch, "method": "react", "truncated": True},
        )
