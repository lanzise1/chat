"""LangChain LLM construction and message conversion."""
from __future__ import annotations

from typing import List

import httpx
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
        timeout=httpx.Timeout(
            connect=settings.llm_connect_timeout,
            read=settings.llm_read_timeout,
            write=10.0,
            pool=5.0,
        ),
        max_retries=0,
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
