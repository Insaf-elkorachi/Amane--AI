from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str = Field(min_length=1)
    message: str = Field(min_length=1)


class ChatResponse(BaseModel):
    session_id: str
    step: str
    response: str
    completed: bool = False
    emergency: bool = False
    collected_data: dict[str, Any] = {}