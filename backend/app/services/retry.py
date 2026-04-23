"""Retry wrapper for opening an LLM stream.

Retry is only safe before the first token reaches the client — once any
delta has been yielded, a retry would duplicate the prefix. So we only
wrap the "open stream + await first chunk" phase.
"""
from __future__ import annotations

import asyncio
from typing import Any, AsyncIterator, List, Tuple

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage
from tenacity import (
    AsyncRetrying,
    retry_if_exception,
    stop_after_attempt,
    wait_random_exponential,
)

from ..core.config import settings
from ..core.errors import is_retryable


async def open_stream_with_retry(
    llm: BaseChatModel,
    messages: List[BaseMessage],
) -> Tuple[Any, AsyncIterator[Any]]:
    """Open a streaming call and return (first_chunk, remaining_stream).

    Retries transient connection / timeout / rate-limit errors until the
    first chunk arrives or attempts are exhausted.
    """
    async for attempt in AsyncRetrying(
        stop=stop_after_attempt(settings.llm_max_attempts),
        wait=wait_random_exponential(
            multiplier=settings.llm_retry_base_delay, max=10
        ),
        retry=retry_if_exception(is_retryable),
        reraise=True,
    ):
        with attempt:
            stream = llm.astream(messages)
            try:
                first = await asyncio.wait_for(
                    stream.__anext__(),
                    timeout=settings.first_token_timeout,
                )
            except BaseException:
                await stream.aclose()
                raise
            return first, stream

    raise RuntimeError("unreachable")


__all__ = ["open_stream_with_retry"]
