"""Deterministic tool helpers used by the route readiness agent."""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class RouteBrief(BaseModel):
    """Condensed brief for a delivery route under development."""

    slug: str
    name: str
    summary: str
    audience_role: str
    audience_experience: Literal["beginner", "intermediate", "advanced"]
    success_metric: str


class DeliveryWindow(BaseModel):
    """Delivery window information tracked by the logistics team."""

    route_slug: str
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


_ROUTE_BRIEFS: dict[str, RouteBrief] = {
    "express-delivery": RouteBrief(
        slug="express-delivery",
        name="Express Delivery Route",
        summary=(
            "Optimized same-day delivery routes for urban areas with time-sensitive packages. "
            "Targets 2-hour delivery windows with real-time tracking."
        ),
        audience_role="Driver",
        audience_experience="intermediate",
        success_metric="95% of deliveries completed within promised window",
    ),
    "cross-country-freight": RouteBrief(
        slug="cross-country-freight",
        name="Cross-Country Freight Route",
        summary=(
            "Long-haul freight optimization for multi-day deliveries across regions. "
            "Focuses on fuel efficiency and driver rest compliance."
        ),
        audience_role="Fleet Manager",
        audience_experience="advanced",
        success_metric="15% reduction in fuel costs while maintaining delivery schedules",
    ),
    "last-mile-delivery": RouteBrief(
        slug="last-mile-delivery",
        name="Last Mile Delivery Route",
        summary=(
            "Final leg delivery optimization for residential areas. "
            "Handles package density, access restrictions, and customer availability."
        ),
        audience_role="Dispatch Coordinator",
        audience_experience="beginner",
        success_metric="Reduce failed delivery attempts by 30%",
    ),
}

_DELIVERY_WINDOWS: dict[str, DeliveryWindow] = {
    "express-delivery": DeliveryWindow(
        route_slug="express-delivery",
        environment="production",
        window_start=date(2025, 1, 15),
        window_end=date(2025, 1, 17),
        freeze_required=True,
        notes="Launch coordinated with marketing campaign for same-day delivery service.",
    ),
    "cross-country-freight": DeliveryWindow(
        route_slug="cross-country-freight",
        environment="production",
        window_start=date(2025, 2, 1),
        window_end=date(2025, 2, 5),
        freeze_required=True,
        notes="Requires driver training completion before rollout.",
    ),
    "last-mile-delivery": DeliveryWindow(
        route_slug="last-mile-delivery",
        environment="staging",
        window_start=date(2025, 1, 20),
        window_end=date(2025, 1, 22),
        freeze_required=False,
        notes="Pilot program in select neighborhoods before full rollout.",
    ),
}

_SUPPORT_DIRECTORY: dict[str, list[SupportContact]] = {
    "Driver": [
        SupportContact(
            audience="Driver",
            contact="driver-support@logistics.example.com",
            escalation_channel="#driver-support",
        ),
        SupportContact(
            audience="Driver",
            contact="safety-team@logistics.example.com",
            escalation_channel="#driver-safety",
        ),
    ],
    "Fleet Manager": [
        SupportContact(
            audience="Fleet Manager",
            contact="fleet-ops@logistics.example.com",
            escalation_channel="#fleet-operations",
        ),
    ],
    "Dispatch Coordinator": [
        SupportContact(
            audience="Dispatch Coordinator",
            contact="dispatch-support@logistics.example.com",
            escalation_channel="#dispatch-help",
        ),
    ],
}

_SLO_WATCH_ITEMS: dict[str, list[str]] = {
    "express-delivery": [
        "Route calculation latency must stay under 500ms",
        "GPS tracking updates required every 30 seconds",
        "Customer notification delivery within 5 seconds of status change",
    ],
    "cross-country-freight": [
        "Driver rest compliance tracking accuracy >99%",
        "Fuel consumption predictions within 5% of actual",
        "Border crossing documentation preparation 24h in advance",
    ],
    "last-mile-delivery": [
        "Address validation accuracy >98%",
        "Package scan-to-delivery time tracking",
        "Customer availability prediction model latency <1s",
    ],
}


def fetch_route_brief(route_slug: str) -> RouteBrief:
    """Return the canonical brief for the requested route."""
    brief = _ROUTE_BRIEFS.get(route_slug)
    if brief is None:
        raise KeyError(route_slug)
    return brief


def fetch_delivery_window(route_slug: str) -> DeliveryWindow:
    """Fetch the delivery window associated with the route."""
    window = _DELIVERY_WINDOWS.get(route_slug)
    if window is None:
        raise KeyError(route_slug)
    return window


def fetch_support_contacts(audience_role: str) -> list[SupportContact]:
    """Return the set of contacts who should be looped in for updates."""
    contacts = _SUPPORT_DIRECTORY.get(audience_role)
    if contacts:
        return contacts
    return [
        SupportContact(
            audience=audience_role,
            contact="support@logistics.example.com",
            escalation_channel="#general-support",
        )
    ]


def list_slo_watch_items(route_slug: str) -> list[str]:
    """List performance and reliability signals for the route."""
    return _SLO_WATCH_ITEMS.get(route_slug, [])
