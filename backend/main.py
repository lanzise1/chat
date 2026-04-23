"""ASGI entrypoint — delegates all wiring to `app.create_app()`."""
from __future__ import annotations

from app import create_app
from app.core.config import settings

app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )
