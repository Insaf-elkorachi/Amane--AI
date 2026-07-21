from typing import Any

from pydantic import BaseModel, Field


class VoiceMessageRequest(BaseModel):
    session_id: str = Field(min_length=1)
    transcript: str = Field(min_length=1)
    source: str = "browser_speech_recognition"
    preferred_language: str | None = None


class VoicePipelineStep(BaseModel):
    name: str
    status: str
    detail: str


class VoiceMessageResponse(BaseModel):
    session_id: str
    step: str
    response: str
    completed: bool = False
    emergency: bool = False
    collected_data: dict[str, Any] = {}
    pipeline: list[VoicePipelineStep]
    agent_trace: dict[str, Any] = {}
