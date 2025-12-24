"""Central configuration helpers for the FastAPI backend.

This module keeps environment handling in one place so the rest of the
application can rely on typed settings rather than scattered calls to
``os.getenv``.
"""

from __future__ import annotations

import os


class Settings:
    """Runtime configuration loaded from environment variables."""

    database_url: str
    cors_origins: list[str]
    gemini_api_key: str | None
    groq_api_key: str | None

    def __init__(self) -> None:
        self.database_url = os.getenv(
            "DATABASE_URL", "postgresql+psycopg2://logistics:logistics@db:5432/logistics",
        )
        origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:8080,http://localhost")
        self.cors_origins = [origin.strip() for origin in origins.split(",") if origin.strip()]
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.groq_api_key = os.getenv("GROQ_API_KEY")


# Create a single instance that will be imported everywhere
_settings = None

def get_settings() -> Settings:
    """Return the Settings instance used across the app."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
