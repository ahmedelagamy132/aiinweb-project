"""Agent endpoints that power the route readiness workflow.

This router uses LangChain-based agent implementation with:
- Gemini/Groq-powered AI insights for route recommendations
- FAISS-based RAG for retrieving relevant documentation
- Database persistence for auditing and learning from past runs
- Historical data access for reviewing previous agent executions
"""

from __future__ import annotations

import os
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.rag import build_retriever

# Use LangChain agent by default, fallback to original if needed
USE_LANGCHAIN = os.getenv("USE_LANGCHAIN_AGENT", "true").lower() == "true"

if USE_LANGCHAIN:
    from app.services.agent_langchain import (
        AgentRunContext,
        AgentRunResult,
        AgentServiceError,
        get_agent_history,
        run_route_readiness_agent,
    )
else:
    from app.services.agent import (
        AgentRunContext,
        AgentRunResult,
        AgentServiceError,
        get_agent_history,
        run_route_readiness_agent,
    )

router = APIRouter(prefix="/ai", tags=["ai"])


class AgentHistoryItem(BaseModel):
    """Simplified view of a historical agent run."""

    id: int
    route_slug: str
    audience_role: str
    summary: str
    gemini_insight: str | None
    used_gemini: bool
    created_at: str


class AgentHistoryResponse(BaseModel):
    """Response containing historical agent runs."""

    runs: list[AgentHistoryItem]
    total: int


@router.post("/route-readiness", response_model=AgentRunResult)
def route_readiness(
    payload: AgentRunContext,
    db: Session = Depends(get_db),
) -> AgentRunResult:
    """Run the AI-powered agent pipeline and surface structured output.

    This endpoint orchestrates:
    1. Tool calls to gather route, delivery window, and contact data
    2. FAISS-based RAG retrieval for relevant documentation
    3. Gemini AI insight generation (when API key is configured)
    4. Database persistence for auditing
    """
    try:
        return run_route_readiness_agent(payload, db=db)
    except AgentServiceError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/history", response_model=AgentHistoryResponse)
def agent_history(
    route_slug: str | None = Query(None, description="Filter by route slug"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of runs to return"),
    db: Session = Depends(get_db),
) -> AgentHistoryResponse:
    """Retrieve historical agent runs from the database.

    This endpoint allows reviewing past agent executions for:
    - Auditing and compliance
    - Learning from previous recommendations
    - Analyzing patterns in route readiness assessments
    """
    runs = get_agent_history(db, route_slug=route_slug, limit=limit)
    items = [
        AgentHistoryItem(
            id=run.id,
            route_slug=run.route_slug,
            audience_role=run.audience_role,
            summary=run.summary,
            gemini_insight=run.gemini_insight,
            used_gemini=run.used_gemini,
            created_at=run.created_at.isoformat(),
        )
        for run in runs
    ]
    return AgentHistoryResponse(runs=items, total=len(items))


@router.get("/routes")
def list_available_routes() -> dict[str, Any]:
    """List available routes that the agent can analyze.

    This endpoint helps the frontend populate dropdowns and
    provides metadata about supported routes.
    """
    from app.services.agent_tools import _ROUTE_BRIEFS, _DELIVERY_WINDOWS

    routes = []
    for slug, brief in _ROUTE_BRIEFS.items():
        window = _DELIVERY_WINDOWS.get(slug)
        routes.append({
            "slug": slug,
            "name": brief.name,
            "summary": brief.summary,
            "audience_role": brief.audience_role,
            "has_delivery_window": window is not None,
            "delivery_date": window.window_start.isoformat() if window else None,
        })

    return {"routes": routes, "total": len(routes)}


class SearchResult(BaseModel):
    """Single document search result."""
    content: str
    source: str
    score: float


class SearchResponse(BaseModel):
    """Response containing search results."""
    results: list[SearchResult]
    query: str
    total: int


@router.get("/search", response_model=SearchResponse)
def search_documents(
    query: str = Query(..., description="Search query for semantic retrieval"),
    k: int = Query(5, ge=1, le=20, description="Number of results to return"),
    db: Session = Depends(get_db),
) -> SearchResponse:
    """Search the knowledge base using semantic similarity.
    
    This endpoint allows direct access to the RAG system for exploring
    logistics documentation, best practices, and operational guidelines.
    """
    if not query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    retriever = build_retriever(db)
    docs = retriever.search(query, k=k)
    
    results = [
        SearchResult(
            content=doc.content,
            source=doc.source,
            score=round(doc.score, 4)
        )
        for doc in docs
    ]
    
    return SearchResponse(
        results=results,
        query=query,
        total=len(results)
    )

