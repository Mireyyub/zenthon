"""Agent Manager – production vs experimental (Faza 5)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Type

from core.logger import logger
from core.event_bus import event_bus
from core.exceptions import AgentError
from agents.base import BaseAgent, AgentResult

# Production agent type names
PRODUCTION_TYPES = {"react", "coding"}


class AgentManager:
    def __init__(self):
        self._agents: Dict[str, BaseAgent] = {}
        self._registry: Dict[str, Type[BaseAgent]] = {}
        self._meta: Dict[str, Dict[str, Any]] = {}

    def register_type(
        self,
        type_name: str,
        agent_cls: Type[BaseAgent],
        *,
        production: bool = False,
        experimental: bool = True,
    ) -> None:
        self._registry[type_name] = agent_cls
        self._meta[type_name] = {
            "production": production or type_name in PRODUCTION_TYPES,
            "experimental": experimental and type_name not in PRODUCTION_TYPES,
        }
        logger.info(
            f"AgentManager: registered '{type_name}' "
            f"prod={self._meta[type_name]['production']}"
        )

    def create(
        self,
        type_name: str,
        name: Optional[str] = None,
        allow_experimental: bool = True,
        **kwargs,
    ) -> BaseAgent:
        if type_name not in self._registry:
            raise AgentError(
                f"Unknown agent type: {type_name}. Available: {list(self._registry)}"
            )
        meta = self._meta.get(type_name, {})
        if meta.get("experimental") and not allow_experimental:
            raise AgentError(
                f"Agent '{type_name}' experimental-dir; allow_experimental=True lazımdır"
            )
        cls = self._registry[type_name]
        agent = cls(name=name or type_name, **kwargs)
        self._agents[agent.id] = agent
        event_bus.publish(
            "AgentCreated",
            {"agent_id": agent.id, "type": type_name, "name": agent.name, **meta},
            source="agents",
        )
        return agent

    def get(self, agent_id: str) -> Optional[BaseAgent]:
        return self._agents.get(agent_id)

    def list_agents(self) -> List[Dict[str, Any]]:
        return [a.info() for a in self._agents.values()]

    def list_types(self, production_only: bool = False) -> List[str]:
        if not production_only:
            return list(self._registry.keys())
        return [k for k, m in self._meta.items() if m.get("production")]

    def list_types_detailed(self) -> List[Dict[str, Any]]:
        return [
            {"type": k, **self._meta.get(k, {})}
            for k in self._registry
        ]

    def run(self, agent_id: str, task: str, context: Optional[Dict] = None) -> AgentResult:
        agent = self._agents.get(agent_id)
        if not agent:
            raise AgentError(f"Agent not found: {agent_id}")
        agent.start()
        try:
            result = agent.run(task, context)
            event_bus.publish(
                "AgentTaskCompleted",
                {"agent_id": agent_id, "success": result.success},
                source="agents",
            )
            return result
        finally:
            agent.stop()

    def remove(self, agent_id: str) -> bool:
        if agent_id in self._agents:
            del self._agents[agent_id]
            return True
        return False


agent_manager = AgentManager()


def _register_defaults():
    # Production
    from agents.react_agent import ReActAgent
    from agents.coding_agent import CodingAgent

    agent_manager.register_type("react", ReActAgent, production=True, experimental=False)
    agent_manager.register_type("coding", CodingAgent, production=True, experimental=False)

    # Optional production-ish helpers if present
    try:
        from agents.research_agent import ResearchAgent

        agent_manager.register_type("research", ResearchAgent, production=False, experimental=True)
    except Exception:
        pass
    try:
        from agents.executor_agent import ExecutorAgent

        agent_manager.register_type("executor", ExecutorAgent, production=False, experimental=True)
    except Exception:
        pass

    # Experimental
    for mod, name, cls_name in [
        ("agents.vision_agent", "vision", "VisionAgent"),
        ("agents.voice_agent", "voice", "VoiceAgent"),
        ("agents.pev", "pev", "PEVAgent"),
        ("agents.reflexion", "reflexion", "ReflexionAgent"),
    ]:
        try:
            import importlib

            m = importlib.import_module(mod)
            cls = getattr(m, cls_name)
            agent_manager.register_type(name, cls, production=False, experimental=True)
        except Exception:
            pass


_register_defaults()
