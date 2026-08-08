"""Smoke imports for Drive-integrated modules."""


def test_rag_import():
    from brain.rag.pipeline import RAGPipeline, TextChunker

    c = TextChunker(chunk_size=64, overlap=8)
    chunks = c.chunk("Daş mövcuddur. Alma meyvədir. Bu üçüncü cümlədir.", "d1")
    assert len(chunks) >= 1
    rag = RAGPipeline()
    rag.ingest_text("Alma meyvədir. Armud da meyvədir.", source="test")
    ctx = rag.retrieve("meyvə")
    assert ctx.total_chunks >= 1


def test_conversation_import():
    from memory.conversation_manager import ConversationManager

    cm = ConversationManager()
    cm.add("user", "salam")
    cm.add("assistant", "salam")
    assert "user" in cm.as_context()


def test_blackboard_import():
    from agents.blackboard import TaskBlackboard

    bb = TaskBlackboard(task_id="t1", original_task="test")
    bb.add_fact("hello", source="test", confidence=0.9)
    assert "hello" in bb.facts_text()


def test_cache_import():
    from brain.llm.cache import LRUCache

    c = LRUCache(maxsize=8)
    c.set("k", "v")
    assert c.get("k") == "v"


def test_swarm_import():
    from agents.swarm import AgentSwarm, AgentRole

    assert AgentRole.RESEARCHER.value == "researcher"
    assert AgentSwarm is not None
