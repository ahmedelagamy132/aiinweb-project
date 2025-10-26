"""Planner endpoints powering structured JSON exercises in Lab 04."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from app.schemas.planner import Plan, PlanRequest, PlanValidationResult
from app.services.planner import build_plan, validate_plan_payload

router = APIRouter(prefix="/planner", tags=["planner"])


@router.post("/plan", response_model=Plan)
def generate_plan(payload: PlanRequest) -> Plan:
    """Return a structured plan tailored to the requested audience."""

    return build_plan(payload)


@router.post("/plan/validate", response_model=PlanValidationResult)
def validate_plan(payload: dict[str, Any]) -> PlanValidationResult:
    """Validate or repair arbitrary plan JSON provided by the caller."""

    try:
        return validate_plan_payload(payload)
    except ValueError as exc:  # Surface repair failures as HTTP 422 errors.
        raise HTTPException(status_code=422, detail=str(exc)) from exc
