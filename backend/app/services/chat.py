"""Chat streaming service — drives a LangGraph agent and emits SSE.

The wire protocol is unchanged from the previous LangChain implementation so
the frontend doesn't need to be touched:
    - {"type": "delta",       "content": "..."}            assistant tokens
    - {"type": "tool_call",   "id", "name", "args"}        model requested a tool
    - {"type": "tool_result", "id", "name", "content"}     tool returned
    - {"type": "done"}                                     end of stream
    - {"type": "error",       "message", "retryable"}      fatal failure

Tool execution and the multi-turn loop now live inside the LangGraph agent;
this module just translates `astream_events(v2)` into our SSE shape.
"""
from __future__ import annotations

import json
from typing import Any, AsyncIterator, List
from uuid import uuid4

from langchain_core.messages import AIMessageChunk

from ..core.errors import is_retryable
from ..schemas.chat import ChatMessage
from ..utils.sse import sse_event
from .graph import get_agent
from .llm import to_lc_messages


def _coerce_delta(delta: object) -> str:
    """Normalize a chunk's content field into a plain string."""
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
    if hasattr(result, "content"):
        inner = result.content
        if isinstance(inner, str):
            return inner
        result = inner
    try:
        return json.dumps(result, ensure_ascii=False, default=str)
    except Exception:  # noqa: BLE001
        return str(result)


async def stream_chat(
    messages: List[ChatMessage],
    thread_id: str | None = None,
) -> AsyncIterator[str]:
    """Yield SSE-formatted events for a chat completion stream.

    When `thread_id` is provided, server-side memory is engaged: the agent
    loads prior turns from the LangGraph checkpointer and only the trailing
    user message is forwarded. Without `thread_id` the call is stateless and
    the full message list is replayed each time.
    """
    try:
        agent = await get_agent()

        if thread_id:
            # Pass only the last message — earlier turns live in the
            # checkpointer keyed by thread_id.
            tail = messages[-1:] if messages else []
            lc_msgs = to_lc_messages(tail)
            effective_thread_id = thread_id
        else:
            # Checkpointer-backed agents require a thread_id on every invoke.
            # Mint a one-shot uuid so the call is effectively stateless: the
            # full history is replayed and nothing prior can be loaded.
            lc_msgs = to_lc_messages(messages)
            effective_thread_id = f"stateless-{uuid4()}"

        invoke_config: dict[str, Any] = {
            "configurable": {"thread_id": effective_thread_id}
        }

        # tool_call events arrive both as accumulating fields on AIMessageChunk
        # and as on_tool_start events; dedupe by id so we never emit twice.
        emitted_tool_calls: set[str] = set()

        async for event in agent.astream_events(
            {"messages": lc_msgs},
            config=invoke_config,
            version="v2",
        ):
            kind = event.get("event")
            data = event.get("data") or {}

            if kind == "on_chat_model_stream":
                chunk: Any = data.get("chunk")
                if chunk is None:
                    continue

                text = _coerce_delta(getattr(chunk, "content", ""))
                if text:
                    yield sse_event({"type": "delta", "content": text})

                if isinstance(chunk, AIMessageChunk):
                    for tc in getattr(chunk, "tool_calls", None) or []:
                        tc_id = tc.get("id") or ""
                        if not tc_id or tc_id in emitted_tool_calls:
                            continue
                        emitted_tool_calls.add(tc_id)
                        yield sse_event(
                            {
                                "type": "tool_call",
                                "id": tc_id,
                                "name": tc.get("name") or "",
                                "args": tc.get("args") or {},
                            }
                        )

            elif kind == "on_tool_start":
                tc_id = event.get("run_id") or ""
                name = event.get("name") or ""
                args = data.get("input") or {}
                if tc_id and tc_id not in emitted_tool_calls:
                    emitted_tool_calls.add(tc_id)
                    yield sse_event(
                        {
                            "type": "tool_call",
                            "id": tc_id,
                            "name": name,
                            "args": args,
                        }
                    )

            elif kind == "on_tool_end":
                tc_id = event.get("run_id") or ""
                name = event.get("name") or ""
                yield sse_event(
                    {
                        "type": "tool_result",
                        "id": tc_id,
                        "name": name,
                        "content": _stringify_tool_result(data.get("output")),
                    }
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
