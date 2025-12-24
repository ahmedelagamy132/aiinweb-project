"""Gemini proxy endpoints for AI-powered content generation."""

from __future__ import annotations

import os
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config import get_settings

router = APIRouter(prefix="/gemini", tags=["gemini"])

try:
    import google.generativeai as genai
except ImportError:
    genai = None


class GenerateRequest(BaseModel):
    """Request payload for content generation."""

    prompt: str
    max_tokens: int = 1024


class GenerateResponse(BaseModel):
    """Response from content generation."""

    content: str
    model: str


@router.post("/generate", response_model=GenerateResponse)
def generate_content(payload: GenerateRequest) -> GenerateResponse:
    """Generate content using Gemini AI.

    This endpoint proxies requests to the Gemini API, generating
    content based on the provided prompt.
    """
    settings = get_settings()

    if not settings.gemini_api_key or genai is None:
        raise HTTPException(
            status_code=503,
            detail="Gemini API not configured. Please set GEMINI_API_KEY environment variable.",
        )

    try:
        genai.configure(api_key=settings.gemini_api_key)
        model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        model = genai.GenerativeModel(model_name)

        response = model.generate_content(payload.prompt)
        content = getattr(response, "text", "").strip()

        return GenerateResponse(content=content, model=model_name)

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Gemini API error: {str(exc)}",
        ) from exc


@router.get("/status")
def gemini_status() -> dict[str, Any]:
    """Check Gemini API configuration status."""
    settings = get_settings()
    return {
        "configured": bool(settings.gemini_api_key),
        "sdk_available": genai is not None,
        "model": os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
    }
