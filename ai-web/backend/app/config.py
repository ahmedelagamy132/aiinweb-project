"""Central configuration helpers for the FastAPI backend.

This module keeps environment handling in one place so the rest of the
application can rely on typed settings rather than scattered calls to
``os.getenv``. The goal is to mirror the structure students will see in
production services: a settings object, sensible defaults, and the ability to
override values via environment variables or a ``.env`` file loaded in
``app.main``.
"""

from __future__ import annotations

import os
from functools import lru_cache


class Settings:
    """Runtime configuration loaded from environment variables."""

    database_url: str
    cors_origins: list[str]
    gemini_api_key: str | None

    def __init__(self) -> None:
        self.database_url = os.getenv(
            "DATABASE_URL", "postgresql+psycopg2://aiweb:aiweb@db:5432/aiweb",
        )
        origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:8080,http://localhost")
        self.cors_origins = [origin.strip() for origin in origins.split(",") if origin.strip()]
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached ``Settings`` instance used across the app."""

    return Settings()

