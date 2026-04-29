"""LangGraph agent factory.

Builds a prebuilt ReAct-style agent on top of `build_llm()` plus the MCP
tools discovered via `mcp_client`. The compiled graph is cached for the life
of the process.

Memory: an in-process `InMemorySaver` is attached so callers can pass
`config={"configurable": {"thread_id": ...}}` to invoke and have the
conversation persisted across requests within this process. Note this is a
dev-grade store — restart drops everything; swap for SqliteSaver /
PostgresSaver in production.
"""
from __future__ import annotations

import asyncio
from typing import Any

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import create_react_agent

from ..core.config import settings
from .llm import build_llm
from .mcp_client import get_mcp_tools

_agent_cache: Any | None = None
_agent_lock = asyncio.Lock()
_checkpointer = InMemorySaver()


async def get_agent() -> Any:
    global _agent_cache
    if _agent_cache is not None:
        return _agent_cache

    async with _agent_lock:
        if _agent_cache is not None:
            return _agent_cache

        tools = await get_mcp_tools()
        _agent_cache = create_react_agent(
            model=build_llm(),
            tools=list(tools),
            prompt=settings.system_prompt,
            checkpointer=_checkpointer,
        )
        return _agent_cache


__all__ = ["get_agent"]
