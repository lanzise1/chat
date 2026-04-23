"""Pydantic schemas for the chat API."""
from __future__ import annotations

from typing import List, Literal

from pydantic import BaseModel, Field

Role = Literal["user", "assistant", "system"]


class ChatMessage(BaseModel):
    role: Role
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage] = Field(..., min_length=1)


class HealthResponse(BaseModel):
    status: str
    model: str
