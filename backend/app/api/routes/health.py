"""Health check route."""
from __future__ import annotations

from fastapi import APIRouter

from ...core.config import settings
from ...schemas.chat import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok", model=settings.openai_model)
