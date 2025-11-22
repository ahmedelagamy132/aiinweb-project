"""Service helpers containing the business logic for the echo endpoints.

The routers import these helpers so that the FastAPI layer remains focused on
HTTP details while the service layer owns the stateful retry simulation.  This
matches the separation of concerns demonstrated in the accompanying lab
notebooks and gives instructors a concrete example to reference in class.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import EchoAttempt


class EchoServiceError(RuntimeError):
    """Raised when the flaky echo service needs to signal a transient failure."""


def get_echo_payload(message: str, db: Session, client_key: str) -> dict[str, str]:
    """Return the provided message wrapped in a JSON-friendly structure."""

    attempt = EchoAttempt(client_key=client_key, failures=0, attempts=1, message=message)
    db.add(attempt)
    db.commit()
    return {"msg": message, "id": attempt.id}


def get_flaky_echo_payload(
    message: str, client_host: str, failures: int, db: Session
) -> dict[str, int | str]:
    """Return the echoed message, simulating transient errors on earlier attempts.

    Args:
        message: The string submitted from the frontend form.
        client_host: A stable identifier for the caller so each student sees their
            own retry counter.
        failures: The number of sequential failures to simulate before success.

    Raises:
        EchoServiceError: If the simulated service is still within the failure
            window and needs the client to retry.
    """

    key = f"{client_host}:{failures}"
    result = db.execute(
        select(EchoAttempt).where(EchoAttempt.client_key == key, EchoAttempt.failures == failures)
    ).scalar_one_or_none()

    if result is None:
        result = EchoAttempt(client_key=key, failures=failures, attempts=0, message=message)
        db.add(result)
        db.commit()
        db.refresh(result)

    if result.attempts < failures:
        result.attempts += 1
        db.add(result)
        db.commit()
        raise EchoServiceError("Simulated transient failure")

    attempts = result.attempts + 1  # Count the successful request as an attempt.
    result.attempts = 0
    result.message = message
    db.add(result)
    db.commit()

    return {"msg": message, "attempts": attempts}
