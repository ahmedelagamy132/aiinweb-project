"""Planner service helpers that keep structured JSON responses consistent."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from pydantic import ValidationError

from app.models import PlanRun
from app.schemas.planner import Plan, PlanRequest, PlanValidationResult, PlanStep

_DEFAULT_STEP_LIBRARY = [
    {
        "title": "Clarify problem statement",
        "description": "Facilitate a working session to confirm the problem this plan solves and document constraints.",
        "owner": "Product Manager",
        "duration_minutes": 45,
        "acceptance_criteria": [
            "Problem statement documented",
            "Constraints captured in shared doc",
        ],
    },
    {
        "title": "Review technical architecture",
        "description": "Pair with the tech lead to outline service boundaries, APIs, and deployment considerations.",
        "owner": "Tech Lead",
        "duration_minutes": 60,
        "acceptance_criteria": [
            "Architecture diagram published",
            "Dependencies reviewed",
        ],
    },
    {
        "title": "Create validation checklist",
        "description": "Draft QA scenarios and monitoring hooks to validate the release before and after launch.",
        "owner": "QA Lead",
        "duration_minutes": 50,
        "acceptance_criteria": [
            "Checklist shared with QA",
            "Observability tasks assigned",
        ],
    },
]

_BEGINNER_STEP = {
    "title": "Schedule enablement workshop",
    "description": "Host a walkthrough to prepare early adopters and gather final questions before launch.",
    "owner": "Developer Advocate",
    "duration_minutes": 40,
    "acceptance_criteria": [
        "Workshop invite sent",
        "Feedback doc created",
    ],
}

_ADVANCED_STEP = {
    "title": "Execute load and chaos rehearsal",
    "description": "Run stress, failover, and rollback drills so production is protected for senior users.",
    "owner": "Site Reliability",
    "duration_minutes": 75,
    "acceptance_criteria": [
        "Load test report archived",
        "Rollback path verified",
    ],
}


def build_plan(request: PlanRequest) -> Plan:
    """Create a structured plan tailored for the requested audience."""

    goal = request.goal.strip()
    audience_role = request.audience_role.strip()
    steps = _compose_steps(goal, request.audience_experience)

    risks: list[str] = []
    if request.primary_risk:
        cleaned_risk = request.primary_risk.strip()
        if cleaned_risk:
            risks.append(cleaned_risk)

    plan = Plan(
        goal=goal,
        audience={"role": audience_role, "experience_level": request.audience_experience},
        steps=[PlanStep(**step) for step in steps],
        risks=risks,
    )
    return plan


def save_plan_run(db: Session, request: PlanRequest, plan: Plan) -> PlanRun:
    """Persist a generated plan so the UI can render historical data."""

    summary = (
        f"Goal: {request.goal} | Audience: {request.audience_role} ({request.audience_experience})"
    )
    run = PlanRun(
        goal=request.goal,
        audience_role=request.audience_role,
        audience_experience=request.audience_experience,
        primary_risk=request.primary_risk,
        include_risks=True,
        summary=summary,
        # Ensure datetimes and other values are JSON-serializable for JSONB storage.
        plan=plan.model_dump(mode="json"),
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def validate_plan_payload(payload: dict[str, Any]) -> PlanValidationResult:
    """Validate or repair arbitrary plan JSON coming from external systems."""

    try:
        plan = Plan.model_validate(payload)
        return PlanValidationResult(
            plan=plan,
            repaired=False,
            messages=["Plan payload validated without changes."],
        )
    except ValidationError as exc:
        repaired_payload = _repair_payload(payload)
        try:
            repaired_plan = Plan.model_validate(repaired_payload)
        except ValidationError as follow_up:
            raise ValueError("Unable to repair plan payload. Please review the submitted structure.") from follow_up

        error_messages = [
            "Original payload failed validation and was automatically repaired.",
            *[
                f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}"
                for error in exc.errors()
            ],
        ]
        return PlanValidationResult(plan=repaired_plan, repaired=True, messages=error_messages)


def _compose_steps(goal: str, experience_level: str) -> list[dict[str, Any]]:
    """Generate plan steps based on the target audience."""

    steps: list[dict[str, Any]] = []
    for template in _DEFAULT_STEP_LIBRARY:
        updated = dict(template)
        updated["description"] = template["description"].replace("this plan", f'"{goal}"')
        steps.append(updated)

    if experience_level == "beginner":
        steps.insert(1, dict(_BEGINNER_STEP))
    elif experience_level == "advanced":
        steps.append(dict(_ADVANCED_STEP))

    for idx, step in enumerate(steps, start=1):
        step.setdefault("acceptance_criteria", [])
        step.setdefault("owner", "Project Lead")
        step.setdefault("duration_minutes", 45)
        step["title"] = step["title"].strip()
        step["description"] = step["description"].strip()
        step.setdefault(
            "acceptance_criteria",
            [f"Step {idx} outputs documented"],
        )
    return steps


def _repair_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Attempt to coerce a loosely structured payload into a valid plan."""

    cleaned_goal = str(payload.get("goal", "Unspecified goal")).strip() or "Unspecified goal"

    audience_data = payload.get("audience")
    if isinstance(audience_data, dict):
        role = str(audience_data.get("role", "Cross-functional team")).strip() or "Cross-functional team"
        experience = audience_data.get("experience_level", "intermediate")
    else:
        role = "Cross-functional team"
        experience = "intermediate"

    if experience not in {"beginner", "intermediate", "advanced"}:
        experience = "intermediate"

    raw_steps = payload.get("steps")
    cleaned_steps: list[dict[str, Any]] = []
    if isinstance(raw_steps, list):
        for index, item in enumerate(raw_steps, start=1):
            if not isinstance(item, dict):
                continue
            title = str(item.get("title") or f"Step {index}").strip() or f"Step {index}"
            description = str(item.get("description") or f"Document progress for {title}.").strip()
            owner = str(item.get("owner") or "Project Lead").strip() or "Project Lead"
            duration = item.get("duration_minutes")
            try:
                duration_int = int(duration)
            except (TypeError, ValueError):
                duration_int = 45
            duration_int = max(5, min(duration_int, 240))

            criteria = item.get("acceptance_criteria")
            if not isinstance(criteria, list):
                criteria = []
            cleaned_criteria = [str(entry).strip() for entry in criteria if str(entry).strip()]
            if not cleaned_criteria:
                cleaned_criteria = [f"Document completion of {title}."]

            cleaned_steps.append(
                {
                    "title": title,
                    "description": description or f"Document progress for {title}.",
                    "owner": owner,
                    "duration_minutes": duration_int,
                    "acceptance_criteria": cleaned_criteria,
                }
            )

    if not cleaned_steps:
        cleaned_steps = _compose_steps(cleaned_goal, "intermediate")

    risks = payload.get("risks")
    cleaned_risks: list[str] = []
    if isinstance(risks, list):
        cleaned_risks = [str(item).strip() for item in risks if str(item).strip()][:3]

    repaired_payload = {
        "goal": cleaned_goal,
        "audience": {"role": role, "experience_level": experience},
        "steps": cleaned_steps,
        "risks": cleaned_risks,
    }
    return repaired_payload
