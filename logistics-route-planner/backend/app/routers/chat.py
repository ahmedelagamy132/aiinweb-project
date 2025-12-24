"""General chat endpoint for natural conversation with the AI agent.

This router provides a flexible chat interface where users can ask any
logistics-related question without being constrained by specific routes or roles.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.chat_agent import run_chat_agent

# LLM imports
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
except ImportError:
    ChatGoogleGenerativeAI = None

try:
    from langchain_openai import ChatOpenAI
except ImportError:
    ChatOpenAI = None

import os
from app.config import get_settings


router = APIRouter(prefix="/ai", tags=["ai"])


class ChatMessage(BaseModel):
    """A single chat message."""
    question: str = Field(..., min_length=1, max_length=2000)


class ToolCall(BaseModel):
    """Information about a tool that was called."""
    tool: str
    arguments: dict[str, Any]
    output: str


class ChatResponse(BaseModel):
    """Response from the chat agent."""
    answer: str
    tool_calls: list[ToolCall] = []
    rag_contexts: list[dict[str, Any]] = []


def _get_llm():
    """Get the configured LLM (Gemini or Groq)."""
    settings = get_settings()
    
    # Try Gemini first
    if settings.gemini_api_key and ChatGoogleGenerativeAI:
        return ChatGoogleGenerativeAI(
            model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
            google_api_key=settings.gemini_api_key,
            temperature=0.7,
        )
    
    # Try Groq (via OpenAI-compatible API)
    if settings.groq_api_key and ChatOpenAI:
        return ChatOpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=settings.groq_api_key,
            model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            temperature=0.7,
        )
    
    raise RuntimeError("No LLM configured. Set GEMINI_API_KEY or GROQ_API_KEY")


@router.post("/chat", response_model=ChatResponse)
def chat(message: ChatMessage, db: Session = Depends(get_db)) -> ChatResponse:
    """
    General-purpose chat endpoint for logistics questions.
    
    The agent has access to:
    - Weather conditions (real-time via OpenWeatherMap)
    - Route metrics calculation (duration, fuel, costs)
    - Traffic conditions analysis
    - Distance calculations between stops
    - Stop sequence optimization
    - Web search capabilities (DuckDuckGo, Wikipedia)
    - RAG-based knowledge base (logistics documentation)
    
    Examples:
    - "What's the weather in Los Angeles?"
    - "Calculate metrics for a 150km route with 8 stops"
    - "Check traffic conditions for Highway 101"
    - "Optimize my delivery stops"
    - "How do I handle time windows?"
    """
    try:
        result = run_chat_agent(message.question, db)
        return ChatResponse(
            answer=result.answer,
            tool_calls=[tc.model_dump() for tc in result.tool_calls],
            rag_contexts=[rc.model_dump() for rc in result.rag_contexts]
        )
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat agent error: {str(e)}")
