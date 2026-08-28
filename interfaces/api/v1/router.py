"""
Leon /api/v1 gateway (Phase 3–5).

All handlers call the same cognitive path as legacy routes.
Tasks: durable SQLite when available.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

from interfaces.api.v1.schemas import (
    AgentRunBody,
    AudioBody,
    ChatBody,
    CrewBody,
    CycleBody,
    MediaGenerateBody,
    MediaUnderstandBody,
    OrchestrateBody,
    ReasonBody,
    RetrieveBody,
    SelfImproveBody,
    TaskCreateBody,
    TeachBody,
    ThinkBody,
    ToolCallBody,
)
from interfaces.api.v1.tasks_store import task_store

api_v1_router = APIRouter(prefix="/api/v1", tags=["v1"])


@api_v1_router.get("/health")
def v1_health() -> Dict[str, Any]:
    from interfaces.api.health import health_report

    return health_report()


@api_v1_router.get("/status")
def v1_status() -> Dict[str, Any]:
    try:
        from core.bootstrap import leon_status

        return leon_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_v1_router.get("/system/status")
def v1_system_status() -> Dict[str, Any]:
    return v1_status()


@api_v1_router.get("/native-core/status")
def v1_native_core() -> Dict[str, Any]:
    from native_core import health_report

    return health_report()


def _think_payload(result: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "answer": result.get("answer") or result.get("conclusion"),
        "confidence": result.get("confidence"),
        "confidence_label": result.get("confidence_label"),
        "source": result.get("source"),
        "trace_id": result.get("trace_id"),
        "decision": result.get("decision"),
        "evidence": result.get("evidence"),
        "llm_used": result.get("llm_used"),
        "agent": result.get("agent"),
        "reasoning_mode": result.get("reasoning_mode"),
    }


@api_v1_router.post("/chat")
def v1_chat(body: ChatBody) -> Dict[str, Any]:
    try:
        from brain.orchestrator import BrainOrchestrator
        from core.config import config

        orch = BrainOrchestrator(brain_name=getattr(config, "ai_name", "Leon") or "Leon")
        result = orch.run(
            body.message,
            goal=body.goal,
            reasoning_mode=body.mode,
            agent_type=body.agent,
            use_session=bool(body.session_id),
        )
        out = _think_payload(result)
        out["session_id"] = body.session_id
        return out
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_v1_router.post("/think")
def v1_think(body: ThinkBody) -> Dict[str, Any]:
    try:
        from brain.orchestrator import BrainOrchestrator
        from core.config import config

        orch = BrainOrchestrator(brain_name=getattr(config, "ai_name", "Leon") or "Leon")
        result = orch.run(
            body.query,
            goal=body.goal,
            reasoning_mode=body.mode,
            agent_type=body.agent,
            use_session=body.use_session,
        )
        return _think_payload(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_v1_router.post("/reason")
def v1_reason(body: ReasonBody) -> Dict[str, Any]:
    try:
        from brain.reasoning.engine import reasoning_engine

        return reasoning_engine.reason(
            body.query,
            strategy=body.strategy,
            goal=body.goal,
            use_brain=body.use_brain,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_v1_router.post("/cycle")
def v1_cycle(body: CycleBody) -> Dict[str, Any]:
    try:
        from brain.cognitive_cycle import CognitiveCycle

        return CognitiveCycle().run(
            body.query,
            goal=body.goal,
            image_path=body.image_path,
            audio_path=body.audio_path,
            agent_type=body.agent,
            learn=body.learn,
            reflect=body.reflect,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_v1_router.get("/agents")
def v1_list_agents() -> Dict[str, Any]:
    try:
        from agents.manager import agent_manager

        names = list(getattr(agent_manager, "list_agents", lambda: [])() or [])
        if not names and hasattr(agent_manager, "_agents"):
            names = list(getattr(agent_manager, "_agents", {}).keys())
        production = ["react", "coding"]
        return {
            "agents": names or production,
            "production": production,
            "experimental": [n for n in names if n not in production],
        }
    except Exception as e:
        return {"agents": ["react", "coding"], "production": ["react", "coding"], "error": str(e)}


@api_v1_router.post("/agents/run")
def v1_agent_run(body: AgentRunBody) -> Dict[str, Any]:
    try:
        from agents.manager import agent_manager

        agent = agent_manager.get(body.agent)
        if agent is None:
            raise HTTPException(status_code=404, detail=f"agent not found: {body.agent}")
        result = agent.run(body.task, context=body.context or {})
        if hasattr(result, "__dict__"):
            return {
                "success": getattr(result, "success", False),
                "output": getattr(result, "output", None),
                "error": getattr(result, "error", None),
                "metadata": getattr(result, "metadata", {}) or {},
                "agent": body.agent,
            }
        return {"result": result, "agent": body.agent}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_v1_router.post("/agents/orchestrate")
def v1_orchestrate(body: OrchestrateBody) -> Dict[str, Any]:
    try:
        from agents.unified_orchestrator import unified_orchestrator

        return unified_orchestrator.run(body.task, agents=body.agents, context=body.context)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_v1_router.post("/agents/crew")
def v1_crew(body: CrewBody) -> Dict[str, Any]:
    try:
        from agents.crew import run_crew

        tasks = [{"description": body.goal, "agent": a} for a in (body.agents or ["react"])]
        return run_crew(body.goal, tasks, mode=body.mode)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_v1_router.get("/tasks")
def v1_list_tasks(limit: int = Query(50, ge=1, le=200)) -> Dict[str, Any]:
    items = [t.to_dict() for t in task_store.list(limit=limit)]
    return {"tasks": items, "count": len(items), "durable": task_store.durable}


@api_v1_router.post("/tasks")
def v1_create_task(body: TaskCreateBody) -> Dict[str, Any]:
    task = task_store.create(
        body.title,
        goal=body.goal,
        action=body.action,
        params=body.params,
        priority=body.priority,
        agent_name=body.agent_name,
    )
    return {"task": task.to_dict(), "durable": task_store.durable}


@api_v1_router.get("/tasks/{task_id}")
def v1_get_task(task_id: str) -> Dict[str, Any]:
    task = task_store.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="task not found")
    return {"task": task.to_dict(), "durable": task_store.durable}


@api_v1_router.get("/storage/status")
def v1_storage_status() -> Dict[str, Any]:
    try:
        from core.storage import migration_status

        return migration_status()
    except Exception as e:
        return {"ok": False, "error": str(e)}


@api_v1_router.post("/storage/migrate")
def v1_storage_migrate() -> Dict[str, Any]:
    try:
        from core.storage import migrate_json_to_sqlite

        return migrate_json_to_sqlite()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_v1_router.post("/memory/retrieve")
def v1_memory_retrieve(body: RetrieveBody) -> Dict[str, Any]:
    try:
        from memory.retrieve import retrieve

        hits = retrieve(body.query, limit=body.limit)
        if isinstance(hits, dict):
            return hits
        return {"query": body.query, "results": hits}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_v1_router.get("/knowledge/facts")
def v1_facts(limit: int = Query(20, ge=1, le=200)) -> Dict[str, Any]:
    try:
        from knowledge.registry import get_fact_store

        fs = get_fact_store()
        all_facts = fs.all() if hasattr(fs, "all") else []
        items = list(all_facts)[:limit]
        out = []
        for f in items:
            if isinstance(f, dict):
                out.append(f)
            elif hasattr(f, "__dict__"):
                out.append(dict(f.__dict__))
            else:
                out.append({"value": str(f)})
        return {"facts": out, "count": len(out)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_v1_router.get("/knowledge/graph")
def v1_graph_stats() -> Dict[str, Any]:
    try:
        from knowledge.registry import get_graph

        g = get_graph()
        stats = g.stats() if hasattr(g, "stats") else {}
        return {"graph": stats, "ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_v1_router.get("/volumes")
def v1_volumes() -> Dict[str, Any]:
    try:
        from curriculum import CurriculumEngine, load_volume

        eng = CurriculumEngine()
        items = []
        for vid in eng.list_volumes():
            try:
                items.append(load_volume(vid))
            except Exception as e:
                items.append({"volume": vid, "error": str(e)})
        return {"volumes": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_v1_router.post("/teach")
def v1_teach(body: TeachBody) -> Dict[str, Any]:
    try:
        from curriculum import CurriculumEngine
        from core.bootstrap import save_state

        eng = CurriculumEngine()
        if body.teach_volume or (body.volume_id and not body.lesson_id):
            report = eng.teach_volume(body.volume_id or "01")
        else:
            report = eng.teach(body.lesson_id or "000001", volume_id=body.volume_id)
        try:
            save_state("api_v1_teach")
        except Exception:
            pass
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_v1_router.post("/self/improve")
def v1_self_improve(body: SelfImproveBody) -> Dict[str, Any]:
    try:
        from brain.self_learning_sync import sync_self_learning

        return sync_self_learning(topic=body.topic, apply=body.apply)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_v1_router.get("/self/view")
def v1_self_view() -> Dict[str, Any]:
    try:
        from brain.self_view import SelfView

        sv = SelfView()
        if hasattr(sv, "summary"):
            return {"view": sv.summary()}
        if hasattr(sv, "body_map"):
            return {"view": sv.body_map()}
        if hasattr(sv, "organs"):
            return {"view": {"organs": list(sv.organs()) if callable(sv.organs) else sv.organs}}
        return {"view": {"status": "available", "hint": "use CLI: self body"}}
    except Exception as e:
        return {"view": None, "error": str(e)}


@api_v1_router.get("/models")
def v1_models() -> Dict[str, Any]:
    try:
        from brain.llm import get_llm_provider

        p = get_llm_provider()
        health = p.health()
        return {
            "provider": health.provider,
            "reachable": health.reachable,
            "offline": health.offline,
            "model": health.model,
            "models": health.models,
            "error": health.error,
        }
    except Exception as e:
        return {"provider": "unknown", "reachable": False, "error": str(e)}


@api_v1_router.get("/tools")
def v1_list_tools() -> Dict[str, Any]:
    try:
        from tools.registry import tool_registry

        names = []
        if hasattr(tool_registry, "list_tools"):
            names = list(tool_registry.list_tools() or [])
        elif hasattr(tool_registry, "_tools"):
            names = list(getattr(tool_registry, "_tools", {}).keys())
        return {"tools": names, "gated": True}
    except Exception as e:
        return {"tools": [], "gated": True, "error": str(e)}


@api_v1_router.post("/tools/call")
def v1_tool_call(body: ToolCallBody) -> Dict[str, Any]:
    try:
        from security import safe_tool_call

        result = safe_tool_call(body.name, body.args or {})
        return {"name": body.name, "result": result, "gated": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@api_v1_router.post("/media/understand")
def v1_media_understand(body: MediaUnderstandBody) -> Dict[str, Any]:
    try:
        from multimodal.understand import understand_image

        return understand_image(
            body.path, question=body.question, use_vlm=body.use_vlm, inject_facts=False
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_v1_router.post("/media/generate")
def v1_media_generate(body: MediaGenerateBody) -> Dict[str, Any]:
    try:
        from multimodal.generate import generate_image

        return generate_image(
            body.prompt,
            width=body.width,
            height=body.height,
            style=body.style,
            seed=body.seed,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_v1_router.post("/audio")
def v1_audio(body: AudioBody) -> Dict[str, Any]:
    try:
        from multimodal.audio import understand_speech, generate_speech, audio_available

        if body.mode == "status":
            return audio_available()
        if body.mode == "stt":
            if not body.path:
                raise HTTPException(status_code=400, detail="path required for stt")
            return understand_speech(body.path)
        if body.mode == "tts":
            return generate_speech(body.text or "")
        return audio_available()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_v1_router.get("/")
def v1_index() -> Dict[str, Any]:
    return {
        "name": "Leon API v1",
        "version": "0.7.0",
        "prefix": "/api/v1",
        "endpoints": [
            "GET  /health",
            "GET  /status",
            "POST /chat",
            "POST /think",
            "POST /reason",
            "GET|POST /tasks",
            "GET  /storage/status",
            "POST /storage/migrate",
            "POST /memory/retrieve",
            "GET  /knowledge/facts",
            "GET  /models",
            "GET  /tools",
            "WS   /ws",
        ],
        "bind_policy": "default 127.0.0.1",
        "storage": "SQLite data/leon/leon.db (JSON dual-read preserved)",
    }
