"""Release readiness agent service orchestrating deterministic tool calls."""

from __future__ import annotations

from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, Field

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
    recommended_actions: list[AgentRecommendation]
    plan: Plan
    tool_calls: list[AgentToolCall]


def run_release_readiness_agent(context: AgentRunContext) -> AgentRunResult:
    """Coordinate tool calls to prepare a release readiness brief."""

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

    plan_request = PlanRequest(
        goal=f"Launch {brief.name} successfully",
        audience_role=context.audience_role,
        audience_experience=context.audience_experience,
        primary_risk=slo_watch_items[0] if context.include_risks and slo_watch_items else None,
    )
    plan: Plan = build_plan(plan_request)

    summary = (
        f"{brief.name} targets {brief.audience_role} personas. "
        f"Production window: {launch_window.window_start:%b %d}–{launch_window.window_end:%b %d}. "
        f"Success metric: {brief.success_metric}."
    )

    recommended_actions: list[AgentRecommendation] = [
        AgentRecommendation(
            title="Confirm launch communications",
            detail=(
                f"Share the feature brief with {contacts[0].contact} and align on messaging for the "
                f"{launch_window.environment} window."
            ),
        ),
        AgentRecommendation(
            title="Validate operational readiness",
            detail=(
                "Ensure runbooks and dashboards reflect the new flow. Coordinate with site reliability "
                "for rollout approval."
            ),
        ),
    ]

    if context.include_risks and slo_watch_items:
        recommended_actions.append(
            AgentRecommendation(
                title="Mitigate top risk",
                detail=f"Create a mitigation plan for: {slo_watch_items[0]}.",
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
            )
        )

    return AgentRunResult(
        summary=summary,
        recommended_actions=recommended_actions,
        plan=plan,
        tool_calls=tool_calls,
    )
