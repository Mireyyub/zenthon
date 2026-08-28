"""Pydantic schemas for /api/v1 (Phase 3)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ThinkBody(BaseModel):
    query: str = Field(..., min_length=1, max_length=8000)
    goal: Optional[str] = None
    mode: str = "auto"
    agent: Optional[str] = None
    use_session: bool = False


class ReasonBody(BaseModel):
    query: str = Field(..., min_length=1, max_length=8000)
    strategy: str = "auto"
    goal: Optional[str] = None
    use_brain: bool = True


class ChatBody(BaseModel):
    """UI-friendly chat: maps to BrainOrchestrator.run."""

    message: str = Field(..., min_length=1, max_length=8000)
    goal: Optional[str] = None
    mode: str = "auto"
    agent: Optional[str] = None
    session_id: Optional[str] = None


class CycleBody(BaseModel):
    query: str = Field(..., min_length=1, max_length=8000)
    goal: Optional[str] = None
    image_path: Optional[str] = None
    audio_path: Optional[str] = None
    agent: Optional[str] = None
    learn: bool = True
    reflect: bool = True


class AgentRunBody(BaseModel):
    task: str = Field(..., min_length=1, max_length=8000)
    agent: str = "react"
    context: Dict[str, Any] = Field(default_factory=dict)


class OrchestrateBody(BaseModel):
    task: str = Field(..., min_length=1, max_length=8000)
    agents: List[str] = Field(default_factory=lambda: ["react", "coding"])
    context: Dict[str, Any] = Field(default_factory=dict)


class CrewBody(BaseModel):
    goal: str = Field(..., min_length=1, max_length=8000)
    mode: str = "sequential"
    agents: List[str] = Field(default_factory=lambda: ["react", "coding"])


class TaskCreateBody(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    goal: str = ""
    action: str = "reason"
    params: Dict[str, Any] = Field(default_factory=dict)
    priority: str = "normal"
    agent_name: Optional[str] = None


class RetrieveBody(BaseModel):
    query: str = Field(..., min_length=1, max_length=4000)
    limit: int = Field(default=8, ge=1, le=50)


class TeachBody(BaseModel):
    lesson_id: Optional[str] = None
    volume_id: Optional[str] = "01"
    teach_volume: bool = False


class SelfImproveBody(BaseModel):
    topic: str = "general"
    apply: bool = False
    volumes: Optional[str] = None  # e.g. "01,02"
    rounds: int = Field(default=1, ge=1, le=10)


class MediaUnderstandBody(BaseModel):
    path: str
    question: Optional[str] = None
    use_vlm: bool = True


class MediaGenerateBody(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=2000)
    width: int = Field(default=512, ge=32, le=2048)
    height: int = Field(default=512, ge=32, le=2048)
    style: str = "auto"
    seed: Optional[int] = None


class AudioBody(BaseModel):
    path: Optional[str] = None
    text: Optional[str] = None
    mode: str = "stt"  # stt | tts | status


class ToolCallBody(BaseModel):
    name: str
    args: Dict[str, Any] = Field(default_factory=dict)
