"""Routes exposing the RAG chatbot experience."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.chatbot import ChatResult, run_chat

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatMessage(BaseModel):
    message: str = Field(..., min_length=2, max_length=2000)


class ChatResponse(BaseModel):
    answer: str
    contexts: list[dict[str, str | float]]
    steps: list[dict[str, str]]
    used_gemini: bool


@router.post("/", response_model=ChatResponse)
def chat(payload: ChatMessage, db: Session = Depends(get_db)) -> ChatResponse:
    """Return a chatbot response enriched with retrieved context."""

    result: ChatResult = run_chat(payload.message, db)
    return ChatResponse(
        answer=result.answer,
        contexts=[{"content": ctx.content, "source": ctx.source, "score": ctx.score} for ctx in result.contexts],
        steps=[{"name": step.name, "detail": step.detail} for step in result.steps],
        used_gemini=result.used_gemini,
    )

