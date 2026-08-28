"""
Agent Swarm — from Drive zenthon_v10, adapted for Leon (sync LLMProvider fallback).
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from core.logger import logger


def _llm_complete(
    prompt: str, system: str = "", temperature: float = 0.3, max_tokens: int = 1024
) -> str:
    try:
        from brain.llm.provider import get_llm_provider

        p = get_llm_provider()
        if p.is_available:
            comp = p.complete(
                prompt, system=system or None, temperature=temperature, max_tokens=max_tokens
            )
            if comp.ok:
                return comp.text
    except Exception as e:
        logger.debug(f"LLM complete failed: {e}")
    return f"[offline] {prompt[:200]}"


class AgentRole(Enum):
    RESEARCHER = "researcher"
    CODER = "coder"
    ANALYST = "analyst"
    WRITER = "writer"
    CRITIC = "critic"
    PLANNER = "planner"


@dataclass
class AgentTask:
    task_id: str
    role: AgentRole
    prompt: str
    context: str = ""
    max_tokens: int = 1024
    temperature: float = 0.3


@dataclass
class AgentResult:
    task_id: str
    role: AgentRole
    content: str
    latency_ms: float
    tokens_used: Optional[int] = None


@dataclass
class SwarmResult:
    query: str
    final_answer: str
    agent_results: List[AgentResult]
    synthesis_latency_ms: float
    total_latency_ms: float
    iterations: int


class Agent:
    def __init__(self, role: AgentRole, system_prompt: Optional[str] = None):
        self.role = role
        self.system_prompt = system_prompt or self._default_prompt(role)

    def _default_prompt(self, role: AgentRole) -> str:
        prompts = {
            AgentRole.RESEARCHER: "Sən tədqiqatçı agentsən. Faktlara əsaslan, qısa cavab ver.",
            AgentRole.CODER: "Sən proqramçı agentsən. İşlək kod təklif et.",
            AgentRole.ANALYST: "Sən analitik agentsən. Müqayisə et, nəticə çıxar.",
            AgentRole.WRITER: "Sən yazıçı agentsən. Aydın Azərbaycan dilində yaz.",
            AgentRole.CRITIC: "Sən tənqidçi agentsən. Zəif cəhətləri göstər.",
            AgentRole.PLANNER: "Sən planlayıcı agentsən. Tapşırığı hissələrə böl.",
        }
        return prompts.get(role, "Sən Leon agentisən.")

    async def execute(self, task: AgentTask) -> AgentResult:
        start = time.time()
        user = task.prompt
        if task.context:
            user = f"Kontekst: {task.context}\n\n{task.prompt}"
        content = ""
        try:
            from brain.llm.async_client import get_async_client

            client = get_async_client()
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user},
            ]
            resp = await client.chat(
                messages, temperature=task.temperature, max_tokens=task.max_tokens
            )
            content = resp if isinstance(resp, str) else str(getattr(resp, "content", resp) or "")
        except Exception:
            content = _llm_complete(
                user,
                system=self.system_prompt,
                temperature=task.temperature,
                max_tokens=task.max_tokens,
            )
        latency = (time.time() - start) * 1000
        return AgentResult(
            task_id=task.task_id, role=self.role, content=content or "", latency_ms=latency
        )


class AgentSwarm:
    def __init__(self):
        self._agents = {role: Agent(role) for role in AgentRole}

    async def run(
        self, query: str, agents: Optional[List[str]] = None, synthesize: bool = True
    ) -> SwarmResult:
        t0 = time.time()
        roles = []
        for name in agents or ["researcher", "analyst"]:
            try:
                roles.append(AgentRole(name))
            except ValueError:
                logger.warning(f"Unknown swarm role: {name}")
        tasks = [
            AgentTask(task_id=f"t{i}", role=r, prompt=query) for i, r in enumerate(roles)
        ]
        results = await asyncio.gather(
            *[self._agents[t.role].execute(t) for t in tasks], return_exceptions=True
        )
        agent_results: List[AgentResult] = []
        for r in results:
            if isinstance(r, AgentResult):
                agent_results.append(r)
            elif isinstance(r, Exception):
                logger.warning(f"Swarm agent error: {r}")

        syn_t0 = time.time()
        if synthesize and agent_results:
            final = await self._synthesize(query, agent_results)
        else:
            final = "\n".join(f"[{a.role.value}] {a.content}" for a in agent_results)
        syn_ms = (time.time() - syn_t0) * 1000
        return SwarmResult(
            query=query,
            final_answer=final,
            agent_results=agent_results,
            synthesis_latency_ms=syn_ms,
            total_latency_ms=(time.time() - t0) * 1000,
            iterations=1,
        )

    async def _synthesize(self, query: str, agent_results: List[AgentResult]) -> str:
        parts = [f"[{r.role.value}]: {r.content}" for r in agent_results]
        prompt = (
            "Agent cavablarını sintez et, təkrarları çıxar.\n\n"
            f"Sual: {query}\n\n" + "\n\n".join(parts) + "\n\nSintez:"
        )
        try:
            from brain.llm.async_client import get_async_client

            client = get_async_client()
            resp = await client.complete(prompt, temperature=0.3, max_tokens=2048)
            if resp:
                return resp.content if hasattr(resp, "content") else str(resp)
        except Exception:
            pass
        return _llm_complete(prompt, temperature=0.3, max_tokens=2048) or "(sintez yox)"

    def run_sync(self, query: str, agents: Optional[List[str]] = None) -> Dict[str, Any]:
        result = asyncio.get_event_loop().run_until_complete(self.run(query, agents=agents))
        return {
            "query": result.query,
            "final_answer": result.final_answer,
            "agents": [
                {"role": a.role.value, "content": a.content, "latency_ms": a.latency_ms}
                for a in result.agent_results
            ],
            "total_latency_ms": result.total_latency_ms,
        }
