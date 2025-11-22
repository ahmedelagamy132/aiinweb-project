"""Chatbot orchestration combining RAG, simple agent steps, and Gemini."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from app.config import get_settings
from app.services import gemini
from app.services.rag import RetrievedContext, build_retriever
from app.services.resources import list_resources

try:  # pragma: no cover - optional dependency
    import google.generativeai as genai
except Exception:  # pragma: no cover
    genai = None


@dataclass
class AgentStep:
    name: str
    detail: str


@dataclass
class ChatResult:
    answer: str
    contexts: list[RetrievedContext]
    steps: list[AgentStep]
    used_gemini: bool


def _build_prompt(message: str, contexts: list[RetrievedContext]) -> str:
    context_block = "\n".join(
        [f"- ({ctx.source}) {ctx.content}" for ctx in contexts]
    )
    instructions = (
        "You are an assistant helping students navigate the AI in Web course. "
        "Use the provided context snippets when they are relevant. If the context "
        "does not answer the question, respond with actionable guidance.""
    )
    return f"{instructions}\n\nContext:\n{context_block}\n\nStudent: {message}\nAssistant:""


def run_chat(message: str, db: Session) -> ChatResult:
    """Run the RAG chatbot and return structured context + response."""

    retriever = build_retriever(db)
    contexts = retriever.search(message, k=4)
    steps: list[AgentStep] = []

    # Lightweight "agent" behaviour: surface course resources when asked.
    if "resource" in message.lower() or "link" in message.lower():
        resources = list_resources(db)[:3]
        summary = ", ".join(resource.title for resource in resources)
        steps.append(AgentStep(name="fetch_resources", detail=f"Suggested: {summary}"))

    settings = get_settings()
    answer = ""
    used_gemini = False
    prompt = _build_prompt(message, contexts)

    if settings.gemini_api_key and genai is not None:
        gemini._configure_client(settings.gemini_api_key)
        model = genai.GenerativeModel("gemini-2.0-flash")
        try:  # pragma: no cover - depends on remote call
            response = model.generate_content(prompt)
            answer = getattr(response, "text", "").strip()
            used_gemini = True
        except Exception as exc:  # pragma: no cover
            answer = (
                "Gemini request failed; falling back to a locally generated summary. "
                f"Error: {exc}"
            )

    if not answer:
        # Fallback deterministic response so the classroom can continue offline.
        combined_sources = "\n".join(ctx.content for ctx in contexts) or "No context available."
        answer = f"(offline preview) Based on the notes: {combined_sources[:400]}"

    return ChatResult(answer=answer, contexts=contexts, steps=steps, used_gemini=used_gemini)

