"""Classification of upstream LLM errors for retry decisions."""
from __future__ import annotations

import asyncio

import httpx
from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    InternalServerError,
    RateLimitError,
)

RETRYABLE_EXCEPTIONS: tuple[type[BaseException], ...] = (
    APIConnectionError,
    APITimeoutError,
    RateLimitError,
    InternalServerError,
    httpx.ConnectError,
    httpx.ReadTimeout,
    httpx.RemoteProtocolError,
    asyncio.TimeoutError,
)

_RETRYABLE_STATUS = {408, 409, 425, 429, 500, 502, 503, 504}


def is_retryable(exc: BaseException) -> bool:
    """True when the caller can safely retry the whole request."""
    if isinstance(exc, RETRYABLE_EXCEPTIONS):
        return True
    if isinstance(exc, APIStatusError):
        return exc.status_code in _RETRYABLE_STATUS
    return False


__all__ = ["is_retryable", "RETRYABLE_EXCEPTIONS"]
