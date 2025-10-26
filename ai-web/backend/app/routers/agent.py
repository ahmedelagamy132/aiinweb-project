"""Agent endpoints that power the Lab 05 release readiness workflow."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.services.agent import (
    AgentRunContext,
    AgentRunResult,
    AgentServiceError,
    run_release_readiness_agent,
)

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/release-readiness", response_model=AgentRunResult)
def release_readiness(payload: AgentRunContext) -> AgentRunResult:
    """Run the deterministic agent pipeline and surface structured output."""

    try:
        return run_release_readiness_agent(payload)
    except AgentServiceError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
