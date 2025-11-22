"""Echo-related API routes used throughout the web programming labs.

The router exposes the lab's simple `/echo` endpoint alongside a `/flaky-echo`
variant that intentionally fails a configurable number of times.  Keeping these
routes in a dedicated module mirrors the folder structure that students build in
Lab 01, where routers, services, and schemas live in their own packages.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from app.database import get_db
from app.models import EchoAttempt
from app.services.echo import EchoServiceError, get_echo_payload, get_flaky_echo_payload
from sqlalchemy import select
from sqlalchemy.orm import Session

router = APIRouter(tags=["echo"])


class EchoIn(BaseModel):
    """Pydantic model describing the request body submitted from the frontend."""

    msg: str


@router.post("/echo")
def echo(payload: EchoIn, request: Request, db: Session = Depends(get_db)) -> dict[str, str]:
    """Return the payload unchanged so students can verify request plumbing."""

    client_host = request.client.host if request.client else "unknown"
    return get_echo_payload(payload.msg, db, client_host)


@router.post("/flaky-echo")
def flaky_echo(
    payload: EchoIn, request: Request, failures: int = 1, db: Session = Depends(get_db)
) -> dict[str, int | str]:
    """Simulate transient failures before eventually returning the echoed message.

    The router delegates the retry tracking to the service layer so the example
    mirrors the lab notes that encourage thin route handlers.
    """

    client_host = request.client.host if request.client else "unknown"

    try:
        return get_flaky_echo_payload(payload.msg, client_host, failures, db)
    except EchoServiceError as exc:  # Translate the domain error into an HTTP error.
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/echo/history", response_model=list[dict[str, str | int]])
def echo_history(db: Session = Depends(get_db)) -> list[dict[str, str | int]]:
    """Return the most recent echo attempts so the frontend can display persistence."""

    attempts = (
        db.execute(select(EchoAttempt).order_by(EchoAttempt.created_at.desc()).limit(10))
        .scalars()
        .all()
    )
    return [
        {
            "id": attempt.id,
            "msg": attempt.message,
            "failures": attempt.failures,
            "attempts": attempt.attempts,
        }
        for attempt in attempts
    ]
