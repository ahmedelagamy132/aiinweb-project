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


class PlanRun(Base):
    """Persist generated plans so students can inspect prior results."""

    __tablename__ = "plan_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    goal: Mapped[str] = mapped_column(String(255))
    audience_role: Mapped[str] = mapped_column(String(120))
    audience_experience: Mapped[str] = mapped_column(String(32))
    primary_risk: Mapped[str | None] = mapped_column(String(255), nullable=True)
    include_risks: Mapped[bool] = mapped_column(Boolean, default=True)
    summary: Mapped[str] = mapped_column(Text)
    plan: Mapped[Any] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Resource(Base):
    """Course resource links surfaced in the new end-to-end feature."""

    __tablename__ = "resources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    url: Mapped[str] = mapped_column(String(500))
    difficulty: Mapped[str] = mapped_column(String(30), default="intermediate")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class DocumentChunk(Base):
    """Indexed content used by the retrieval-augmented chatbot."""

    __tablename__ = "document_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(120), index=True)
    source: Mapped[str] = mapped_column(String(255))
    content: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

