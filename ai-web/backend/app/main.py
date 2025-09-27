"""FastAPI backend powering the lab exercises.

This lightweight service exposes a health check and an echo endpoint that the
frontend labs call during development. CORS middleware is configured so the
Vite dev server can reach the API from a different origin while students test
their work locally.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI() # Initialize the FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Permit the local Vite dev server (List to allow the frontend to use the backend resources)
    allow_methods=["*"], # All methods of request are allowed 
    allow_headers=["*"],
)


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
