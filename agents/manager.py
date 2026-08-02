"""Agent Manager – bütün agent tiplərinin qeydiyyatı."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Type

from core.logger import logger
from core.event_bus import event_bus
from core.exceptions import AgentError
from agents.base import BaseAgent, AgentResult


class AgentManager:
    def __init__(self):
        self._agents: Dict[str, BaseAgent] = {}
        self._registry: Dict[str, Type[BaseAgent]] = {}

    def register_type(self, type_name: str, agent_cls: Type[BaseAgent]) -> None:
        self._registry[type_name] = agent_cls
        logger.info(f"AgentManager: registered type '{type_name}'")

    def create(self, type_name: str, name: Optional[str] = None, **kwargs) -> BaseAgent:
        if type_name not in self._registry:
            raise AgentError(f"Unknown agent type: {type_name}. Available: {list(self._registry)}")
        cls = self._registry[type_name]
        agent = cls(name=name or type_name, **kwargs)
        self._agents[agent.id] = agent
        event_bus.publish(
            "AgentCreated",
            {"agent_id": agent.id, "type": type_name, "name": agent.name},
            source="agents",
        )
        return agent

    def get(self, agent_id: str) -> Optional[BaseAgent]:
        return self._agents.get(agent_id)

    def list_agents(self) -> List[Dict[str, Any]]:
        return [a.info() for a in self._agents.values()]

    def list_types(self) -> List[str]:
        return list(self._registry.keys())

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
    from agents.coding_agent import CodingAgent
    from agents.research_agent import ResearchAgent
    from agents.executor_agent import ExecutorAgent

    agent_manager.register_type("coding", CodingAgent)
    agent_manager.register_type("research", ResearchAgent)
    agent_manager.register_type("executor", ExecutorAgent)

    try:
        from agents.vision_agent import VisionAgent
        agent_manager.register_type("vision", VisionAgent)
    except ImportError:
        pass
    try:
        from agents.voice_agent import VoiceAgent
        agent_manager.register_type("voice", VoiceAgent)
    except ImportError:
        pass
    try:
        from agents.react_agent import ReActAgent
        agent_manager.register_type("react", ReActAgent)
    except ImportError:
        pass
    try:
        from agents.pev import PEVAgent
        agent_manager.register_type("pev", PEVAgent)
    except ImportError:
        pass


_register_defaults()
