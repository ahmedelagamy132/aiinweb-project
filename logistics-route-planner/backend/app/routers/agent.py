"""Agent endpoints for route validation and optimization.

This router uses LangChain-based agent implementation with:
- Real tools: weather API, route calculations, optimization, traffic analysis
- Gemini/Groq-powered AI for route validation recommendations
- FAISS-based RAG for retrieving relevant documentation
- Database persistence for auditing and learning from past runs
"""

from __future__ import annotations

import os
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.rag import build_retriever
from app.schemas.route_planning import RouteRequest, RouteValidationResult

# Use LangChain agent by default
USE_LANGCHAIN = os.getenv("USE_LANGCHAIN_AGENT", "true").lower() == "true"

if USE_LANGCHAIN:
    from app.services.agent_langchain import (
        AgentServiceError,
        get_agent_history,
        run_route_validation_agent,
    )
else:
    # Fallback not implemented for new route planning agent
    from app.services.agent_langchain import (
        AgentServiceError,
        get_agent_history,
        run_route_validation_agent,
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


@router.post("/validate-route", response_model=RouteValidationResult)
def validate_route(
    payload: RouteRequest,
    db: Session = Depends(get_db),
) -> RouteValidationResult:
    """Run AI-powered route validation and optimization.

    This endpoint orchestrates:
    1. Weather API calls for delivery locations
    2. Route metrics calculations (fuel, time, cost)
    3. Time window validation with constraints
    4. Stop sequence optimization by priority
    5. Traffic analysis for route timing
    6. FAISS-based RAG retrieval for best practices
    7. Gemini/Groq AI validation and recommendations
    8. Database persistence for auditing
    """
    try:
        return run_route_validation_agent(payload, db=db)
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
    """List example routes for testing the validation system.

    This endpoint provides sample RouteRequest examples that
    can be used to test the route validation agent.
    """
    examples = [
        {
            "route_id": "RT-001",
            "name": "Downtown Morning Delivery",
            "start_location": "San Francisco Depot",
            "planned_start_time": "2025-12-24T07:00:00Z",
            "num_stops": 8,
            "description": "High-priority deliveries in downtown SF during morning hours"
        },
        {
            "route_id": "RT-002",
            "name": "Suburban Afternoon Route",
            "start_location": "Oakland Warehouse",
            "planned_start_time": "2025-12-24T13:00:00Z",
            "num_stops": 12,
            "description": "Standard deliveries in suburban areas with flexible time windows"
        },
        {
            "route_id": "RT-003",
            "name": "Express Cross-City",
            "start_location": "San Jose Distribution Center",
            "planned_start_time": "2025-12-24T10:00:00Z",
            "num_stops": 5,
            "description": "Urgent deliveries across multiple cities"
        }
    ]

    return {"routes": examples, "total": len(examples)}


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

