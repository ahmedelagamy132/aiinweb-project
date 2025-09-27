"""FastAPI backend powering the lab exercises.

This lightweight service exposes a health check and an echo endpoint that the
frontend labs call during development. CORS middleware is configured so the
Vite dev server can reach the API from a different origin while students test
their work locally.
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI() # Initialize the FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Permit the local Vite dev server (List to allow the frontend to use the backend resources)
    allow_methods=["*"], # All methods of request are allowed 
    allow_headers=["*"],
)


# Track transient failure counts per client to simulate flaky behavior.
_flaky_attempts: dict[str, int] = {}


class EchoIn(BaseModel):
    """Payload schema for `/echo`, carrying the text entered in the labs."""
    msg: str


@app.get("/health")
def health():
    """Report service status for lab curl checks and container health probes."""
    return {"status": "ok"}


@app.post("/echo")
def echo(payload: EchoIn):
    """Echo the provided message so students can verify request/response flows."""
    return {"msg": payload.msg}


@app.post("/flaky-echo")
def flaky_echo(payload: EchoIn, request: Request, failures: int = 1):
    """Simulate transient failures before eventually echoing the payload."""

    client_host = request.client.host if request.client else "unknown"
    key = f"{client_host}:{failures}"
    seen = _flaky_attempts.get(key, 0)

    if seen < failures:
        _flaky_attempts[key] = seen + 1
        raise HTTPException(status_code=503, detail="Simulated transient failure")

    _flaky_attempts[key] = 0
    return {"msg": payload.msg, "attempts": seen + 1}
