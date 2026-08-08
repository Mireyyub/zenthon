"""
agents/local_agi/base_agent.py — Base agent from Drive Leon.təlim Local AGI.
Adapted for zenthon: uses core.logger; LLM via brain.llm.client soft-fallback.
"""
from __future__ import annotations

import json
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from core.logger import logger


class AgentStatus(Enum):
    IDLE = "idle"
    THINKING = "thinking"
    EXECUTING = "executing"
    WAITING = "waiting"
    DONE = "done"
    ERROR = "error"


@dataclass
class AgentMessage:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    from_agent: str = ""
    to_agent: str = ""
    task_id: str = ""
    action: str = ""
    payload: dict = field(default_factory=dict)
    requires_critic: bool = False
    timestamp: float = field(default_factory=time.time)
    priority: int = 5

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "from": self.from_agent,
            "to": self.to_agent,
            "task_id": self.task_id,
            "action": self.action,
            "payload": self.payload,
            "critic_req": self.requires_critic,
            "timestamp": self.timestamp,
            "priority": self.priority,
        }


@dataclass
class AgentResult:
    agent_name: str
    task_id: str
    status: str
    output: Any = None
    error: Optional[str] = None
    duration_ms: float = 0.0
    tokens_used: int = 0
    metadata: dict = field(default_factory=dict)
    confidence: float = 1.0

    @property
    def success(self) -> bool:
        return self.status == "success"

    def to_dict(self) -> dict:
        return {
            "agent": self.agent_name,
            "task_id": self.task_id,
            "status": self.status,
            "output": str(self.output)[:500] if self.output else None,
            "error": self.error,
            "duration_ms": round(self.duration_ms, 2),
            "tokens": self.tokens_used,
            "confidence": round(self.confidence, 2),
        }


@dataclass
class ReflectionResult:
    reaction: str
    content: str
    success: bool = True


class BaseAgent(ABC):
    """Base for Local AGI style agents (planner, reasoner, executor, critic, memory)."""

    def __init__(self, name: str, system_prompt: str = ""):
        self.name = name
        self.system_prompt = system_prompt
        self.status = AgentStatus.IDLE
        self._message_log: list[AgentMessage] = []
        self._result_log: list[AgentResult] = []
        self._consecutive_failures = 0
        self._circuit_open_until = 0.0
        self._failure_threshold = 3
        self._cooldown_seconds = 30
        self.max_retries = 2
        logger.info(f"[{self.name}] Agent started")

    @abstractmethod
    def process(self, task: str, context: Optional[dict] = None) -> AgentResult:
        ...

    def run(self, task: str, context: Optional[dict] = None) -> AgentResult:
        context = dict(context or {})
        task_id = context.get("task_id") or str(uuid.uuid4())[:8]
        context["task_id"] = task_id

        if not self.is_healthy():
            remaining = round(self._circuit_open_until - time.time(), 1)
            return AgentResult(
                agent_name=self.name,
                task_id=task_id,
                status="failed",
                error=f"Circuit open ({remaining}s)",
                metadata={"circuit_open": True},
            )

        self.status = AgentStatus.THINKING
        t_start = time.time()
        bb = context.get("blackboard_context", "")
        effective_task = f"{task}\n\n{bb}" if bb else task

        last_error = None
        for attempt in range(self.max_retries):
            try:
                result = self.process(effective_task, context)
                result.duration_ms = (time.time() - t_start) * 1000
                result.task_id = task_id
                if result.success:
                    self.status = AgentStatus.DONE
                    self._consecutive_failures = 0
                    self._result_log.append(result)
                    return result
                self.status = AgentStatus.ERROR
                self._register_failure()
                self._result_log.append(result)
                return result
            except Exception as e:
                last_error = str(e)
                logger.error(f"[{self.name}] attempt {attempt+1}: {e}")
                time.sleep(min(2 ** attempt, 4))

        self.status = AgentStatus.ERROR
        self._register_failure()
        failed = AgentResult(
            agent_name=self.name,
            task_id=task_id,
            status="failed",
            error=f"retries exhausted: {last_error}",
            duration_ms=(time.time() - t_start) * 1000,
        )
        self._result_log.append(failed)
        return failed

    def is_healthy(self) -> bool:
        if self._circuit_open_until == 0:
            return True
        if time.time() >= self._circuit_open_until:
            self._circuit_open_until = 0.0
            self._consecutive_failures = max(0, self._failure_threshold - 1)
            return True
        return False

    def _register_failure(self) -> None:
        self._consecutive_failures += 1
        if self._consecutive_failures >= self._failure_threshold:
            self._circuit_open_until = time.time() + self._cooldown_seconds
            logger.error(f"[{self.name}] circuit OPEN for {self._cooldown_seconds}s")

    def _parse_json_response(self, response: str) -> Optional[dict]:
        raw = response.strip()
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0].strip()
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            try:
                start, end = raw.find("{"), raw.rfind("}") + 1
                if start >= 0 and end > start:
                    return json.loads(raw[start:end])
            except Exception:
                pass
            return None

    def get_stats(self) -> dict:
        total = len(self._result_log)
        success = sum(1 for r in self._result_log if r.success)
        avg_ms = sum(r.duration_ms for r in self._result_log) / total if total else 0
        return {
            "agent": self.name,
            "status": self.status.value,
            "total_tasks": total,
            "success_rate": f"{success}/{total}",
            "avg_duration": f"{avg_ms:.0f}ms",
            "healthy": self.is_healthy(),
        }
