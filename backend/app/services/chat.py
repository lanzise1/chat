"""Chat streaming service — produces SSE chunks from a LangChain stream."""
from __future__ import annotations

from typing import AsyncIterator, List

from app.schemas.chat import ChatMessage
from app.services.llm import build_llm, to_lc_messages
from app.utils.sse import sse_event


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
    try:
        llm = build_llm()
        lc_msgs = to_lc_messages(messages)

        async for chunk in llm.astream(lc_msgs):
            text = _coerce_delta(chunk.content)
            if text:
                yield sse_event({"type": "delta", "content": text})

        yield sse_event({"type": "done"})
    except Exception as e:  # noqa: BLE001
        yield sse_event({"type": "error", "message": str(e)})
