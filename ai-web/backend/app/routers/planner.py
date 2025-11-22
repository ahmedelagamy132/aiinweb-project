"""Planner endpoints powering structured JSON exercises in Lab 04."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import PlanRun
from app.schemas.planner import Plan, PlanRequest, PlanValidationResult
from app.services.planner import build_plan, save_plan_run, validate_plan_payload

router = APIRouter(prefix="/planner", tags=["planner"])


@router.post("/plan", response_model=Plan)
def generate_plan(payload: PlanRequest, db: Session = Depends(get_db)) -> Plan:
    """Return a structured plan tailored to the requested audience."""

    plan = build_plan(payload)
    save_plan_run(db, payload, plan)
    return plan


@router.post("/plan/validate", response_model=PlanValidationResult)
def validate_plan(payload: dict[str, Any]) -> PlanValidationResult:
    """Validate or repair arbitrary plan JSON provided by the caller."""

    try:
        return validate_plan_payload(payload)
    except ValueError as exc:  # Surface repair failures as HTTP 422 errors.
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/plan/history", response_model=list[dict[str, Any]])
def list_plans(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    """Return recently generated plans to demonstrate persistence."""

    runs = db.execute(select(PlanRun).order_by(PlanRun.created_at.desc()).limit(10)).scalars().all()
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
