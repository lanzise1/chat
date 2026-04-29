"""LangChain LLM construction and message conversion for the LangGraph agent."""
from __future__ import annotations

from typing import List

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from ..core.config import settings
from ..schemas.chat import ChatMessage


def build_llm() -> ChatOpenAI:
    if not settings.openai_api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Copy .env.example to .env and fill it in."
        )


    return ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        temperature=settings.temperature,
        streaming=True,
        # The gateway doesn't echo usage info, so disabling this avoids a
        # `None + None` TypeError when langchain-openai tries to aggregate
        # token usage across streamed chunks.
        stream_usage=False,
    )


def to_lc_messages(messages: List[ChatMessage]) -> List[BaseMessage]:
    """Convert API ChatMessage list into LangChain messages.

    The system prompt is supplied to the agent via `create_agent(prompt=...)`,
    so it is *not* prepended here.
    """
    lc: List[BaseMessage] = []
    for m in messages:
        if m.role == "user":
            lc.append(HumanMessage(content=m.content))
        elif m.role == "assistant":
            lc.append(AIMessage(content=m.content))
        elif m.role == "system":
            lc.append(SystemMessage(content=m.content))
    return lc
