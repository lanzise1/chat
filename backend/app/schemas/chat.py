"""Pydantic schemas for the chat API."""
from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field

Role = Literal["user", "assistant", "system"]


class ChatMessage(BaseModel):
    role: Role
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage] = Field(..., min_length=1)
    # When supplied, server-side memory (LangGraph checkpointer) is used and
    # only the trailing message(s) of `messages` need to be new — prior turns
    # are loaded from the thread. When absent, the request is stateless and
    # the full history must be sent (legacy behavior).
    thread_id: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    model: str
