"""Configuration loaded from environment / .env."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List

from dotenv import load_dotenv

load_dotenv()


def _split_csv(value: str) -> List[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_base_url: str | None = os.getenv("OPENAI_BASE_URL") or None
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    temperature: float = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))

    llm_connect_timeout: float = float(os.getenv("LLM_CONNECT_TIMEOUT", "5"))
    llm_read_timeout: float = float(os.getenv("LLM_READ_TIMEOUT", "60"))
    first_token_timeout: float = float(os.getenv("FIRST_TOKEN_TIMEOUT", "20"))
    chunk_timeout: float = float(os.getenv("CHUNK_TIMEOUT", "30"))
    llm_max_attempts: int = int(os.getenv("LLM_MAX_ATTEMPTS", "3"))
    llm_retry_base_delay: float = float(os.getenv("LLM_RETRY_BASE_DELAY", "1"))

    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))

    cors_origins: List[str] = field(
        default_factory=lambda: _split_csv(
            os.getenv("CORS_ORIGINS", "http://localhost:5173")
        )
    )

    system_prompt: str = os.getenv(
        "SYSTEM_PROMPT",
        "You are a helpful AI assistant. "
        "When it helps readability, respond in GitHub-flavored Markdown "
        "(code blocks with language tags, lists, tables, etc.).",
    )


settings = Settings()
