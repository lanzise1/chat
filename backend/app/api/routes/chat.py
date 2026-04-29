"""Chat streaming route."""
from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from ...schemas.chat import ChatRequest
from ...services.chat import stream_chat

router = APIRouter()

_SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "X-Accel-Buffering": "no",  # disable nginx buffering
    "Connection": "keep-alive",
}


@router.post("/chat")
async def chat(req: ChatRequest) -> StreamingResponse:
    return StreamingResponse(
        stream_chat(req.messages, thread_id=req.thread_id),
        media_type="text/event-stream",
        headers=_SSE_HEADERS,
    )
