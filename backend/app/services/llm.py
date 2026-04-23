"""LangChain LLM construction and message conversion."""
from __future__ import annotations

from typing import List

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.schemas.chat import ChatMessage


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
    )


def to_lc_messages(messages: List[ChatMessage]) -> List[BaseMessage]:
    """Convert API ChatMessage list into LangChain messages, prepending the system prompt."""
    lc: List[BaseMessage] = [SystemMessage(content=settings.system_prompt)]
    for m in messages:
        if m.role == "user":
            lc.append(HumanMessage(content=m.content))
        elif m.role == "assistant":
            lc.append(AIMessage(content=m.content))
        elif m.role == "system":
            lc.append(SystemMessage(content=m.content))
    return lc
