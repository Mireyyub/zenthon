"""Phase 1 domain contracts — must stay green."""

from __future__ import annotations


def test_event_name_stable_strings():
    from core.contracts import EventName, make_event_payload

    assert EventName.USER_MESSAGE.value == "user.message"
    assert EventName.TASK_COMPLETED.value == "task.completed"
    p = make_event_payload(EventName.REASON_COMPLETED, {"answer": "x"}, source="test")
    assert p.name == "reason.completed"
    assert p.data["answer"] == "x"
    d = p.to_dict()
    assert "event_id" in d and "timestamp" in d


def test_task_lifecycle():
    from core.contracts import Task, TaskStatus, TaskResult, new_task_id

    t = Task(id=new_task_id(), title="demo", goal="test", action="reason")
    assert t.status == TaskStatus.PENDING
    t.mark_running()
    assert t.status == TaskStatus.RUNNING
    assert t.started_at is not None
    t.mark_done(TaskResult(success=True, output="ok"))
    assert t.status == TaskStatus.DONE
    assert t.progress == 1.0
    assert t.result is not None and t.result.success

    raw = t.to_dict()
    t2 = Task.from_dict(raw)
    assert t2.id == t.id
    assert t2.status == TaskStatus.DONE


def test_task_fail_and_cancel():
    from core.contracts import Task, TaskStatus, new_task_id

    t = Task(id=new_task_id(), title="f")
    t.mark_failed("boom")
    assert t.status == TaskStatus.FAILED
    assert t.error == "boom"

    t2 = Task(id=new_task_id(), title="c")
    t2.mark_cancelled()
    assert t2.status == TaskStatus.CANCELLED


def test_agent_message_roundtrip():
    from core.contracts import AgentMessage, AgentMessageKind, AgentRole

    m = AgentMessage.make(
        AgentMessageKind.DECISION,
        AgentRole.PLANNER,
        "do X",
        agent_name="planner",
        confidence=0.9,
    )
    d = m.to_dict()
    m2 = AgentMessage.from_dict(d)
    assert m2.kind == AgentMessageKind.DECISION
    assert m2.role == AgentRole.PLANNER
    assert m2.content == "do X"
    assert 0.89 <= m2.confidence <= 0.91


def test_mock_provider():
    from brain.llm.provider import MockProvider, get_llm_provider

    p = MockProvider(fixed_reply="hello")
    c = p.complete("anything")
    assert c.ok
    assert c.text == "hello"
    assert c.provider == "mock"
    h = p.health()
    assert h.reachable is True
    assert h.offline is True

    p2 = get_llm_provider(prefer="mock")
    assert p2.name == "mock"


def test_ollama_provider_wraps_client_without_crash():
    """Must not raise even if Ollama is down — returns error completion."""
    from brain.llm.provider import OllamaProvider, LLMCompletion

    p = OllamaProvider()
    result = p.complete("Say ok", max_tokens=5)
    assert isinstance(result, LLMCompletion)
    # Either real reply or honest error — never exception
    assert result.provider == "ollama"
    h = p.health()
    assert h.provider == "ollama"
    assert isinstance(h.reachable, bool)


def test_plan_task_bridge():
    from brain.planning.schema import PlanTask
    from core.contracts import Task

    pt = PlanTask(id="T-abc", title="teach vol", action="teach", params={"vol": "01"})
    t = Task.from_plan_task(pt, plan_id="P-1", goal="learn")
    assert t.id == "T-abc"
    assert t.action == "teach"
    assert t.plan_id == "P-1"
    assert t.goal == "learn"
