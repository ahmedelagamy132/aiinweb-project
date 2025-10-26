"""Deterministic tool helpers used by the release readiness agent."""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class FeatureBrief(BaseModel):
    """Condensed product brief for a feature under development."""

    slug: str
    name: str
    summary: str
    audience_role: str
    audience_experience: Literal["beginner", "intermediate", "advanced"]
    success_metric: str


class LaunchWindow(BaseModel):
    """Deployment window information tracked by the release team."""

    feature_slug: str
    environment: Literal["staging", "production"]
    window_start: date
    window_end: date
    freeze_required: bool = Field(default=True)
    notes: str = Field(default="")


class SupportContact(BaseModel):
    """Contact details for teams who need proactive updates."""

    audience: str
    contact: str
    escalation_channel: str


_FEATURE_BRIEFS: dict[str, FeatureBrief] = {
    "curriculum-pathways": FeatureBrief(
        slug="curriculum-pathways",
        name="Curriculum Pathways",
        summary=(
            "Surface sequenced lab recommendations so instructors can scaffold lessons "
            "for students based on prior completions."
        ),
        audience_role="Instructor",
        audience_experience="intermediate",
        success_metric="90% of instructors adopt generated pathways for the next cohort",
    ),
    "team-analytics": FeatureBrief(
        slug="team-analytics",
        name="Team Analytics Dashboard",
        summary="Deliver a consolidated dashboard that highlights agent usage and completion trends for admins.",
        audience_role="Program Manager",
        audience_experience="advanced",
        success_metric="Daily active program managers increase by 25%",
    ),
}

_LAUNCH_WINDOWS: dict[str, LaunchWindow] = {
    "curriculum-pathways": LaunchWindow(
        feature_slug="curriculum-pathways",
        environment="production",
        window_start=date(2025, 3, 10),
        window_end=date(2025, 3, 12),
        freeze_required=True,
        notes="Coordinated release with marketing webinar on Mar 11.",
    ),
    "team-analytics": LaunchWindow(
        feature_slug="team-analytics",
        environment="production",
        window_start=date(2025, 4, 2),
        window_end=date(2025, 4, 4),
        freeze_required=True,
        notes="Requires feature flag rollout 48 hours prior to launch.",
    ),
}

_SUPPORT_DIRECTORY: dict[str, list[SupportContact]] = {
    "Instructor": [
        SupportContact(
            audience="Instructor",
            contact="education-success@example.com",
            escalation_channel="#instructor-support",
        ),
        SupportContact(
            audience="Instructor",
            contact="pedagogy-lead@example.com",
            escalation_channel="#curriculum-updates",
        ),
    ],
    "Program Manager": [
        SupportContact(
            audience="Program Manager",
            contact="program-ops@example.com",
            escalation_channel="#program-ops",
        ),
    ],
}

_SLO_WATCH_ITEMS: dict[str, list[str]] = {
    "curriculum-pathways": [
        "Lesson ingestion latency must stay under 2 minutes",
        "Planner responses require >95% schema compliance",
    ],
    "team-analytics": [
        "Dashboard queries should resolve under 1.5 seconds",
        "Background aggregation jobs must remain below 75% CPU utilization",
    ],
}


def fetch_feature_brief(feature_slug: str) -> FeatureBrief:
    """Return the canonical product brief for the requested feature."""

    brief = _FEATURE_BRIEFS.get(feature_slug)
    if brief is None:
        raise KeyError(feature_slug)
    return brief


def fetch_launch_window(feature_slug: str) -> LaunchWindow:
    """Fetch the release window associated with the feature."""

    window = _LAUNCH_WINDOWS.get(feature_slug)
    if window is None:
        raise KeyError(feature_slug)
    return window


def fetch_support_contacts(audience_role: str) -> list[SupportContact]:
    """Return the set of contacts who should be looped in for updates."""

    contacts = _SUPPORT_DIRECTORY.get(audience_role)
    if contacts:
        return contacts
    return [
        SupportContact(
            audience=audience_role,
            contact="success@example.com",
            escalation_channel="#general-updates",
        )
    ]


def list_slo_watch_items(feature_slug: str) -> list[str]:
    """List performance and reliability signals for the feature."""

    return _SLO_WATCH_ITEMS.get(feature_slug, [])
