"""Chat streaming service — produces SSE chunks from a LangChain stream.

Supports MCP tool calling:
  - tools are discovered once from the configured MCP server
  - `llm.bind_tools(tools)` lets the model emit tool_calls mid-stream
  - after each streamed turn we inspect tool_calls, invoke them via MCP,
    append ToolMessage results, and let the model continue up to
    MCP_MAX_TOOL_ITERATIONS rounds
"""
from __future__ import annotations

import asyncio
import json
from typing import Any, AsyncIterator, List

from langchain_core.messages import AIMessageChunk, ToolMessage

from ..core.config import settings
from ..core.errors import is_retryable
from ..schemas.chat import ChatMessage
from ..utils.sse import sse_event
from .llm import build_llm, to_lc_messages
from .mcp_client import get_mcp_tools
from .retry import open_stream_with_retry


def _coerce_delta(delta: object) -> str:
    """Normalize LangChain chunk content to a plain string."""
    if isinstance(delta, str):
        return delta
    if isinstance(delta, list):
        return "".join(
            part.get("text", "") for part in delta if isinstance(part, dict)
        )
    return ""


def _stringify_tool_result(result: object) -> str:
    if isinstance(result, str):
        return result
    try:
        return json.dumps(result, ensure_ascii=False, default=str)
    except Exception:  # noqa: BLE001
        return str(result)


async def stream_chat(messages: List[ChatMessage]) -> AsyncIterator[str]:
    """Yield SSE-formatted events for a chat completion stream."""
    stream: AsyncIterator[Any] | None = None
    try:
        base_llm = build_llm()
        tools = await get_mcp_tools()
        tools_by_name = {t.name: t for t in tools}
        llm = base_llm.bind_tools(tools) if tools else base_llm

        lc_msgs = to_lc_messages(messages)

        max_iterations = max(1, settings.mcp_max_tool_iterations)
        for iteration in range(max_iterations):
            chunks: list[AIMessageChunk] = []

            if iteration == 0:
                first, stream = await open_stream_with_retry(llm, lc_msgs)
                chunks.append(first)
                text = _coerce_delta(first.content)
                if text:
                    yield sse_event({"type": "delta", "content": text})
            else:
                stream = llm.astream(lc_msgs)

            while True:
                try:
                    chunk = await asyncio.wait_for(
                        stream.__anext__(),
                        timeout=settings.chunk_timeout,
                    )
                except StopAsyncIteration:
                    break
                chunks.append(chunk)
                text = _coerce_delta(chunk.content)
                if text:
                    yield sse_event({"type": "delta", "content": text})

            try:
                await stream.aclose()
            except Exception:  # noqa: BLE001
                pass
            stream = None

            if not chunks:
                break

            agg: AIMessageChunk = chunks[0]
            for c in chunks[1:]:
                agg = agg + c

            tool_calls = list(getattr(agg, "tool_calls", None) or [])
            if not tool_calls:
                break

            lc_msgs.append(agg)
            for tc in tool_calls:
                name = tc.get("name") or ""
                args = tc.get("args") or {}
                tc_id = tc.get("id") or ""

                yield sse_event(
                    {"type": "tool_call", "id": tc_id, "name": name, "args": args}
                )

                tool = tools_by_name.get(name)
                if tool is None:
                    result_text = f"Tool {name!r} is not available."
                else:
                    try:
                        result = await tool.ainvoke(args)
                        result_text = _stringify_tool_result(result)
                    except Exception as e:  # noqa: BLE001
                        result_text = f"Tool {name!r} raised: {e}"

                yield sse_event(
                    {
                        "type": "tool_result",
                        "id": tc_id,
                        "name": name,
                        "content": result_text,
                    }
                )
                lc_msgs.append(
                    ToolMessage(content=result_text, tool_call_id=tc_id, name=name)
                )

        yield sse_event({"type": "done"})
    except Exception as e:  # noqa: BLE001
        yield sse_event(
            {
                "type": "error",
                "message": str(e),
                "retryable": is_retryable(e),
            }
        )
    finally:
        if stream is not None:
            try:
                await stream.aclose()
            except Exception:  # noqa: BLE001
                pass
