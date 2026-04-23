"""MCP client — loads tools from the configured MCP server.

Tools are cached for the life of the process; they rarely change between
requests and the discovery round-trip would otherwise run on every chat call.
"""
from __future__ import annotations

import asyncio
import logging
from typing import List

from langchain_core.tools import BaseTool

from ..core.config import settings

logger = logging.getLogger(__name__)

_tools_cache: List[BaseTool] | None = None
_tools_lock = asyncio.Lock()


async def get_mcp_tools() -> List[BaseTool]:
    """Return LangChain tools exposed by the configured MCP server.

    Returns an empty list if MCP is disabled or the server is unreachable;
    the caller should treat tool availability as best-effort.
    """
    global _tools_cache

    if not settings.mcp_enabled:
        return []

    if _tools_cache is not None:
        return _tools_cache

    async with _tools_lock:
        if _tools_cache is not None:
            return _tools_cache

        try:
            from langchain_mcp_adapters.client import MultiServerMCPClient

            client = MultiServerMCPClient(
                {
                    "demo": {
                        "transport": "streamable_http",
                        "url": settings.mcp_server_url,
                    }
                }
            )
            tools = await client.get_tools()
            _tools_cache = list(tools)
            logger.info(
                "Loaded %d MCP tool(s) from %s: %s",
                len(_tools_cache),
                settings.mcp_server_url,
                [t.name for t in _tools_cache],
            )
        except Exception as e:  # noqa: BLE001
            logger.warning("MCP tool discovery failed (%s); continuing without tools", e)
            _tools_cache = []

        return _tools_cache


__all__ = ["get_mcp_tools"]
