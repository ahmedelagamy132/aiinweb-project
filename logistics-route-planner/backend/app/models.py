"""SQLAlchemy models representing the application's relational data."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def utcnow() -> datetime:
    """Return a timezone-naive UTC timestamp for created_at columns."""
    return datetime.utcnow()


class EchoAttempt(Base):
    """Track retry attempts for the flaky echo demo on a per-client basis."""

    __tablename__ = "echo_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    client_key: Mapped[str] = mapped_column(String(255), index=True)
    failures: Mapped[int] = mapped_column(Integer, default=1)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    message: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class RouteRun(Base):
    """Persist generated route plans so users can inspect prior results."""

    __tablename__ = "route_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    goal: Mapped[str] = mapped_column(String(255))
    audience_role: Mapped[str] = mapped_column(String(120))
    audience_experience: Mapped[str] = mapped_column(String(32))
    primary_risk: Mapped[str | None] = mapped_column(String(255), nullable=True)
    include_risks: Mapped[bool] = mapped_column(Boolean, default=True)
    summary: Mapped[str] = mapped_column(Text)
    plan: Mapped[Any] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class DocumentChunk(Base):
    """Indexed content used by the retrieval-augmented agent."""

    __tablename__ = "document_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(120), index=True)
    source: Mapped[str] = mapped_column(String(255))
    content: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class AgentRun(Base):
    """Persist agent execution history for auditing and learning from past runs."""

    __tablename__ = "agent_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    route_slug: Mapped[str] = mapped_column(String(120), index=True)
    audience_role: Mapped[str] = mapped_column(String(120))
    audience_experience: Mapped[str] = mapped_column(String(32))
    summary: Mapped[str] = mapped_column(Text)
    gemini_insight: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommended_actions: Mapped[Any] = mapped_column(JSONB)
    tool_calls: Mapped[Any] = mapped_column(JSONB)
    rag_contexts: Mapped[Any] = mapped_column(JSONB, default=list)
    used_gemini: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
