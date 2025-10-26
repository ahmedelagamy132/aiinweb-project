"""Structured planner schemas shared by labs and services."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class PlanAudience(BaseModel):
    """Describe who the plan is designed for so UI copy can adjust."""

    role: str = Field(..., min_length=2, max_length=64)
    experience_level: Literal["beginner", "intermediate", "advanced"]


class PlanStep(BaseModel):
    """Individual step in the generated plan."""

    title: str = Field(..., min_length=3, max_length=120)
    description: str = Field(..., min_length=10, max_length=500)
    owner: str = Field(..., min_length=2, max_length=60)
    duration_minutes: int = Field(..., ge=5, le=240)
    acceptance_criteria: list[str] = Field(default_factory=list)

    @field_validator("acceptance_criteria")
    @classmethod
    def _trim_criteria(cls, value: list[str]) -> list[str]:
        """Remove empty acceptance criteria entries submitted by the client."""

        return [item.strip() for item in value if item.strip()]


class Plan(BaseModel):
    """Top-level plan returned to the frontend."""

    goal: str = Field(..., min_length=3, max_length=160)
    audience: PlanAudience
    created_at: datetime = Field(default_factory=datetime.utcnow)
    version: str = Field(default="1.0.0")
    steps: list[PlanStep] = Field(default_factory=list, min_length=1)
    risks: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _ensure_unique_titles(self) -> "Plan":
        """Guarantee that step titles stay unique for accessible rendering."""

        seen: set[str] = set()
        for step in self.steps:
            if step.title in seen:
                raise ValueError("Step titles must be unique within a plan.")
            seen.add(step.title)
        return self


class PlanRequest(BaseModel):
    """Payload accepted from the UI when requesting a plan."""

    goal: str = Field(..., min_length=3, max_length=160)
    audience_role: str = Field(..., min_length=2, max_length=64)
    audience_experience: Literal["beginner", "intermediate", "advanced"]
    primary_risk: str | None = Field(default=None, max_length=160)


class PlanValidationResult(BaseModel):
    """Response returned after validating or repairing arbitrary payloads."""

    plan: Plan
    repaired: bool = Field(default=False)
    messages: list[str] = Field(default_factory=list)
