"""Echo endpoints demonstrating retry patterns."""

from __future__ import annotations

import random
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import EchoAttempt

router = APIRouter(prefix="/echo", tags=["echo"])


class EchoIn(BaseModel):
    """Payload for the echo endpoint."""

    message: str
    client_key: str | None = None


class EchoOut(BaseModel):
    """Response from the echo endpoint."""

    message: str
    echo: str
    attempts: int


@router.post("", response_model=EchoOut)
def echo(payload: EchoIn, db: Session = Depends(get_db)) -> EchoOut:
    """Echo the message back, with simulated failures to demonstrate retries.

    This endpoint simulates a flaky service that may fail several times
    before succeeding, demonstrating the need for retry logic.
    """
    client_key = payload.client_key or "anonymous"

    # Find or create attempt record
    attempt = db.query(EchoAttempt).filter(
        EchoAttempt.client_key == client_key,
        EchoAttempt.message == payload.message,
    ).first()

    if attempt is None:
        # First attempt - decide how many failures to simulate
        failures = random.randint(1, 3)
        attempt = EchoAttempt(
            client_key=client_key,
            message=payload.message,
            failures=failures,
            attempts=1,
        )
        db.add(attempt)
        db.commit()
        db.refresh(attempt)
    else:
        attempt.attempts += 1
        db.commit()
        db.refresh(attempt)

    # Simulate failure if not enough attempts yet
    if attempt.attempts <= attempt.failures:
        raise HTTPException(
            status_code=503,
            detail=f"Service temporarily unavailable (attempt {attempt.attempts}/{attempt.failures + 1})",
        )

    return EchoOut(
        message=payload.message,
        echo=payload.message,
        attempts=attempt.attempts,
    )


@router.delete("/reset/{client_key}")
def reset_attempts(client_key: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Reset attempt tracking for a specific client."""
    deleted = db.query(EchoAttempt).filter(EchoAttempt.client_key == client_key).delete()
    db.commit()
    return {"deleted": deleted, "client_key": client_key}
