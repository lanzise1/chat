"""Chat streaming service — produces SSE chunks from a LangChain stream."""
from __future__ import annotations

import asyncio
from typing import Any, AsyncIterator, List

from ..core.config import settings
from ..core.errors import is_retryable
from ..schemas.chat import ChatMessage
from ..utils.sse import sse_event
from .llm import build_llm, to_lc_messages
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


async def stream_chat(messages: List[ChatMessage]) -> AsyncIterator[str]:
    """Yield SSE-formatted events for a chat completion stream."""
    stream: AsyncIterator[Any] | None = None
    try:
        llm = build_llm()
        lc_msgs = to_lc_messages(messages)

        first, stream = await open_stream_with_retry(llm, lc_msgs)

        text = _coerce_delta(first.content)
        if text:
            yield sse_event({"type": "delta", "content": text})

        while True:
            try:
                chunk = await asyncio.wait_for(
                    stream.__anext__(),
                    timeout=settings.chunk_timeout,
                )
            except StopAsyncIteration:
                break
            text = _coerce_delta(chunk.content)
            if text:
                yield sse_event({"type": "delta", "content": text})

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
