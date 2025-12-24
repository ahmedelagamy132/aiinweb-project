"""Planner endpoints for generating and validating route plans."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import RouteRun
from app.schemas.planner import RoutePlan, RouteRequest, RouteValidationResult
from app.services.planner import build_route_plan, save_route_run, validate_route_payload

router = APIRouter(prefix="/planner", tags=["planner"])


@router.post("/route", response_model=RoutePlan)
def generate_route_plan(payload: RouteRequest, db: Session = Depends(get_db)) -> RoutePlan:
    """Return a structured route plan tailored to the requested audience."""
    plan = build_route_plan(payload)
    save_route_run(db, payload, plan)
    return plan


@router.post("/route/validate", response_model=RouteValidationResult)
def validate_route(payload: dict[str, Any]) -> RouteValidationResult:
    """Validate or repair arbitrary route plan JSON provided by the caller."""
    try:
        return validate_route_payload(payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/route/history", response_model=list[dict[str, Any]])
def list_route_plans(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    """Return recently generated route plans to demonstrate persistence."""
    runs = db.execute(select(RouteRun).order_by(RouteRun.created_at.desc()).limit(10)).scalars().all()
    return [
        {
            "id": run.id,
            "goal": run.goal,
            "audience_role": run.audience_role,
            "audience_experience": run.audience_experience,
            "summary": run.summary,
            "plan": run.plan,
        }
        for run in runs
    ]
