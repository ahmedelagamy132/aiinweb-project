"""Release readiness agent service integrating Gemini AI, FAISS RAG, and database.

This module demonstrates a production-grade agent architecture that:
1. Gathers context from multiple tools (feature briefs, launch windows, contacts)
2. Retrieves relevant documentation using FAISS-backed RAG
3. Uses Gemini to generate intelligent insights and recommendations
4. Persists all agent runs to the database for auditing and learning
"""

from __future__ import annotations

import os
from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import AgentRun
from app.schemas.planner import Plan, PlanRequest
from app.services.agent_tools import (
    FeatureBrief,
    LaunchWindow,
    SupportContact,
    fetch_feature_brief,
    fetch_launch_window,
    fetch_support_contacts,
    list_slo_watch_items,
)
from app.services.planner import build_plan
from app.services.rag import RetrievedContext, build_retriever

try:
    import google.generativeai as genai
except ImportError:
    genai = None


class AgentServiceError(RuntimeError):
    """Raised when the agent cannot complete its workflow."""


class AgentToolCall(BaseModel):
    """Trace of a tool invocation the agent performed."""

    tool: str
    arguments: dict[str, Any]
    output_preview: str


class AgentRecommendation(BaseModel):
    """Action item recommended by the agent."""

    title: str
    detail: str
    priority: Literal["high", "medium", "low"] = "medium"


class RAGContext(BaseModel):
    """Retrieved context from the FAISS index."""

    content: str
    source: str
    score: float


class AgentRunContext(BaseModel):
    """Input payload submitted by the frontend."""

    feature_slug: str = Field(..., min_length=2, max_length=40)
    launch_date: date
    audience_role: str = Field(..., min_length=2, max_length=60)
    audience_experience: Literal["beginner", "intermediate", "advanced"]
    include_risks: bool = Field(default=True)


class AgentRunResult(BaseModel):
    """Structured result returned to the frontend."""

    summary: str
    gemini_insight: str | None = None
    recommended_actions: list[AgentRecommendation]
    plan: Plan
    tool_calls: list[AgentToolCall]
    rag_contexts: list[RAGContext] = []
    used_gemini: bool = False


def _generate_gemini_insight(
    brief: FeatureBrief,
    launch_window: LaunchWindow,
    slo_items: list[str],
    rag_contexts: list[RetrievedContext],
    context: AgentRunContext,
) -> tuple[str | None, list[AgentRecommendation]]:
    """Use Gemini to generate intelligent insights based on gathered context.

    Returns a tuple of (insight_text, ai_recommendations).
    """
    settings = get_settings()
    if not settings.gemini_api_key or genai is None:
        return None, []

    try:
        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel(os.getenv("GEMINI_MODEL", "gemini-2.0-flash"))

        # Build rich context from all sources
        context_parts = [
            f"Feature: {brief.name}",
            f"Summary: {brief.summary}",
            f"Target Audience: {brief.audience_role} ({brief.audience_experience})",
            f"Success Metric: {brief.success_metric}",
            f"Launch Window: {launch_window.window_start} to {launch_window.window_end}",
            f"Environment: {launch_window.environment}",
            f"Freeze Required: {launch_window.freeze_required}",
        ]

        if slo_items:
            context_parts.append(f"SLO Watch Items: {', '.join(slo_items)}")

        if rag_contexts:
            rag_text = "\n".join([f"- ({ctx.source}) {ctx.content}" for ctx in rag_contexts])
            context_parts.append(f"Related Documentation:\n{rag_text}")

        full_context = "\n".join(context_parts)

        prompt = f"""You are a release readiness advisor helping teams prepare for feature launches.
Based on the following context, provide:
1. A brief strategic insight (2-3 sentences) about the launch readiness
2. Two specific AI-generated recommendations with priority levels

Context:
{full_context}

User's Launch Date: {context.launch_date}
Include Risk Analysis: {context.include_risks}

Respond in this exact format:
INSIGHT: <your strategic insight here>
RECOMMENDATION_1: <title>|<detail>|<priority: high/medium/low>
RECOMMENDATION_2: <title>|<detail>|<priority: high/medium/low>"""

        response = model.generate_content(prompt)
        response_text = getattr(response, "text", "").strip()

        # Parse the response
        insight = ""
        ai_recommendations: list[AgentRecommendation] = []

        for line in response_text.split("\n"):
            line = line.strip()
            if line.startswith("INSIGHT:"):
                insight = line[8:].strip()
            elif line.startswith("RECOMMENDATION_"):
                parts = line.split(":", 1)
                if len(parts) > 1:
                    rec_parts = parts[1].strip().split("|")
                    if len(rec_parts) >= 3:
                        priority = rec_parts[2].strip().lower()
                        if priority not in ("high", "medium", "low"):
                            priority = "medium"
                        ai_recommendations.append(
                            AgentRecommendation(
                                title=f"[AI] {rec_parts[0].strip()}",
                                detail=rec_parts[1].strip(),
                                priority=priority,
                            )
                        )

        return insight if insight else None, ai_recommendations

    except Exception as exc:
        # Log but don't fail the agent if Gemini is unavailable
        print(f"Gemini insight generation failed: {exc}")
        return None, []


def run_release_readiness_agent(
    context: AgentRunContext,
    db: Session | None = None,
) -> AgentRunResult:
    """Coordinate tool calls, RAG retrieval, and Gemini to prepare a release readiness brief.

    This agent demonstrates a complete integration of:
    - Deterministic tool calls for structured data gathering
    - FAISS-based RAG for retrieving relevant documentation
    - Gemini AI for generating intelligent insights
    - Database persistence for auditing and learning
    """

    try:
        brief: FeatureBrief = fetch_feature_brief(context.feature_slug)
    except KeyError as exc:
        raise AgentServiceError(f"Unknown feature '{context.feature_slug}'.") from exc

    try:
        launch_window: LaunchWindow = fetch_launch_window(context.feature_slug)
    except KeyError as exc:
        raise AgentServiceError(
            f"Launch window data is missing for feature '{context.feature_slug}'."
        ) from exc

    contacts: list[SupportContact] = fetch_support_contacts(context.audience_role)
    slo_watch_items: list[str] = list_slo_watch_items(context.feature_slug)

    # Track tool calls for transparency
    tool_calls = [
        AgentToolCall(
            tool="fetch_feature_brief",
            arguments={"feature_slug": context.feature_slug},
            output_preview=f"{brief.name}: {brief.summary}",
        ),
        AgentToolCall(
            tool="fetch_launch_window",
            arguments={"feature_slug": context.feature_slug},
            output_preview=(
                f"{launch_window.environment} window {launch_window.window_start.isoformat()}"
                f" → {launch_window.window_end.isoformat()}"
            ),
        ),
        AgentToolCall(
            tool="fetch_support_contacts",
            arguments={"audience_role": context.audience_role},
            output_preview=f"{len(contacts)} contact(s) notified",
        ),
    ]

    if slo_watch_items:
        tool_calls.append(
            AgentToolCall(
                tool="list_slo_watch_items",
                arguments={"feature_slug": context.feature_slug},
                output_preview=", ".join(slo_watch_items[:2]),
            )
        )

    # RAG: Retrieve relevant documentation using FAISS
    rag_contexts: list[RetrievedContext] = []
    if db is not None:
        retriever = build_retriever(db)
        search_query = f"{brief.name} {context.audience_role} release launch"
        rag_contexts = retriever.search(search_query, k=3)
        if rag_contexts:
            tool_calls.append(
                AgentToolCall(
                    tool="rag_retrieval",
                    arguments={"query": search_query, "k": 3},
                    output_preview=f"Retrieved {len(rag_contexts)} relevant document(s)",
                )
            )

    # Generate Gemini insight if available
    gemini_insight, ai_recommendations = _generate_gemini_insight(
        brief, launch_window, slo_watch_items, rag_contexts, context
    )
    used_gemini = gemini_insight is not None

    if used_gemini:
        insight_preview = ""
        if gemini_insight:
            insight_preview = gemini_insight[:100] + "..." if len(gemini_insight) > 100 else gemini_insight
        tool_calls.append(
            AgentToolCall(
                tool="gemini_insight_generation",
                arguments={"model": os.getenv("GEMINI_MODEL", "gemini-2.0-flash")},
                output_preview=insight_preview,
            )
        )

    # Build the plan
    plan_request = PlanRequest(
        goal=f"Launch {brief.name} successfully",
        audience_role=context.audience_role,
        audience_experience=context.audience_experience,
        primary_risk=slo_watch_items[0] if context.include_risks and slo_watch_items else None,
    )
    plan: Plan = build_plan(plan_request)

    # Generate summary
    summary = (
        f"{brief.name} targets {brief.audience_role} personas. "
        f"Production window: {launch_window.window_start:%b %d}–{launch_window.window_end:%b %d}. "
        f"Success metric: {brief.success_metric}."
    )

    # Build deterministic recommendations
    recommended_actions: list[AgentRecommendation] = [
        AgentRecommendation(
            title="Confirm launch communications",
            detail=(
                f"Share the feature brief with {contacts[0].contact} and align on messaging for the "
                f"{launch_window.environment} window."
            ),
            priority="high",
        ),
        AgentRecommendation(
            title="Validate operational readiness",
            detail=(
                "Ensure runbooks and dashboards reflect the new flow. Coordinate with site reliability "
                "for rollout approval."
            ),
            priority="high",
        ),
    ]

    if context.include_risks and slo_watch_items:
        recommended_actions.append(
            AgentRecommendation(
                title="Mitigate top risk",
                detail=f"Create a mitigation plan for: {slo_watch_items[0]}.",
                priority="high",
            )
        )

    if len(contacts) > 1:
        recommended_actions.append(
            AgentRecommendation(
                title="Broadcast stakeholder update",
                detail=(
                    "Send a tailored update to secondary contacts so downstream teams can prepare "
                    "training materials and support docs."
                ),
                priority="medium",
            )
        )

    # Add AI-generated recommendations
    recommended_actions.extend(ai_recommendations)

    # Convert RAG contexts to response format
    rag_context_response = [
        RAGContext(content=ctx.content, source=ctx.source, score=ctx.score)
        for ctx in rag_contexts
    ]

    result = AgentRunResult(
        summary=summary,
        gemini_insight=gemini_insight,
        recommended_actions=recommended_actions,
        plan=plan,
        tool_calls=tool_calls,
        rag_contexts=rag_context_response,
        used_gemini=used_gemini,
    )

    # Persist agent run to database for auditing
    if db is not None:
        agent_run = AgentRun(
            feature_slug=context.feature_slug,
            audience_role=context.audience_role,
            audience_experience=context.audience_experience,
            summary=summary,
            gemini_insight=gemini_insight,
            recommended_actions=[rec.model_dump() for rec in recommended_actions],
            tool_calls=[tc.model_dump() for tc in tool_calls],
            rag_contexts=[ctx.model_dump() for ctx in rag_context_response],
            used_gemini=used_gemini,
        )
        db.add(agent_run)
        db.commit()

    return result


def get_agent_history(db: Session, feature_slug: str | None = None, limit: int = 10) -> list[AgentRun]:
    """Retrieve historical agent runs from the database."""
    from sqlalchemy import select

    query = select(AgentRun).order_by(AgentRun.created_at.desc()).limit(limit)
    if feature_slug:
        query = query.where(AgentRun.feature_slug == feature_slug)
    return list(db.execute(query).scalars().all())
