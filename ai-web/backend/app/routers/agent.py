"""Agent endpoints that power the Lab 05 release readiness workflow.

This router demonstrates a production-grade agent API with:
- Gemini-powered AI insights for release recommendations
- FAISS-based RAG for retrieving relevant documentation
- Database persistence for auditing and learning from past runs
- Historical data access for reviewing previous agent executions
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.agent import (
    AgentRunContext,
    AgentRunResult,
    AgentServiceError,
    get_agent_history,
    run_release_readiness_agent,
)

router = APIRouter(prefix="/ai", tags=["ai"])


class AgentHistoryItem(BaseModel):
    """Simplified view of a historical agent run."""

    id: int
    feature_slug: str
    audience_role: str
    summary: str
    gemini_insight: str | None
    used_gemini: bool
    created_at: str


class AgentHistoryResponse(BaseModel):
    """Response containing historical agent runs."""

    runs: list[AgentHistoryItem]
    total: int


@router.post("/release-readiness", response_model=AgentRunResult)
def release_readiness(
    payload: AgentRunContext,
    db: Session = Depends(get_db),
) -> AgentRunResult:
    """Run the AI-powered agent pipeline and surface structured output.

    This endpoint orchestrates:
    1. Tool calls to gather feature, launch window, and contact data
    2. FAISS-based RAG retrieval for relevant documentation
    3. Gemini AI insight generation (when API key is configured)
    4. Database persistence for auditing

    The response includes both deterministic recommendations and AI-generated
    insights when Gemini is available.
    """

    try:
        return run_release_readiness_agent(payload, db=db)
    except AgentServiceError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/history", response_model=AgentHistoryResponse)
def agent_history(
    feature_slug: str | None = Query(None, description="Filter by feature slug"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of runs to return"),
    db: Session = Depends(get_db),
) -> AgentHistoryResponse:
    """Retrieve historical agent runs from the database.

    This endpoint allows reviewing past agent executions for:
    - Auditing and compliance
    - Learning from previous recommendations
    - Analyzing patterns in release readiness assessments
    """

    runs = get_agent_history(db, feature_slug=feature_slug, limit=limit)
    items = [
        AgentHistoryItem(
            id=run.id,
            feature_slug=run.feature_slug,
            audience_role=run.audience_role,
            summary=run.summary,
            gemini_insight=run.gemini_insight,
            used_gemini=run.used_gemini,
            created_at=run.created_at.isoformat(),
        )
        for run in runs
    ]
    return AgentHistoryResponse(runs=items, total=len(items))


@router.get("/features")
def list_available_features() -> dict[str, Any]:
    """List available features that the agent can analyze.

    This endpoint helps the frontend populate dropdowns and
    provides metadata about supported features.
    """
    from app.services.agent_tools import _FEATURE_BRIEFS, _LAUNCH_WINDOWS

    features = []
    for slug, brief in _FEATURE_BRIEFS.items():
        window = _LAUNCH_WINDOWS.get(slug)
        features.append({
            "slug": slug,
            "name": brief.name,
            "summary": brief.summary,
            "audience_role": brief.audience_role,
            "has_launch_window": window is not None,
            "launch_date": window.window_start.isoformat() if window else None,
        })

    return {"features": features, "total": len(features)}
