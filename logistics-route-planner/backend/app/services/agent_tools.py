"""Real LangChain tools for the route readiness agent.

This module implements proper LangChain tools using the @tool decorator,
allowing the agent to use them dynamically with AgentExecutor.
"""

from __future__ import annotations

from datetime import date
from typing import Literal, Optional
import json

from langchain_core.tools import tool
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


# =============================================================================
# LANGCHAIN TOOL IMPLEMENTATIONS
# These are decorated with @tool to make them proper LangChain tools
# =============================================================================

@tool
def fetch_route_brief(route_slug: str) -> str:
    """Fetch detailed information about a specific delivery route.
    
    Use this tool to get comprehensive details about a route including:
    - Route name and summary
    - Target audience and experience level
    - Success metrics and KPIs
    
    Args:
        route_slug: The unique identifier for the route (e.g., 'express-delivery', 
                   'cross-country-freight', 'last-mile-delivery')
    
    Returns:
        JSON string with route details including name, summary, audience, and metrics
    """
    brief = _ROUTE_BRIEFS.get(route_slug)
    if brief is None:
        return json.dumps({"error": f"Route '{route_slug}' not found. Available routes: {list(_ROUTE_BRIEFS.keys())}"})
    return json.dumps(brief.model_dump(), indent=2)


@tool
def fetch_delivery_window(route_slug: str) -> str:
    """Get delivery window and deployment timeline information for a route.
    
    Use this tool to check:
    - Deployment environment (staging/production)
    - Start and end dates for the delivery window
    - Whether a deployment freeze is required
    - Important notes about the timeline
    
    Args:
        route_slug: The route identifier to check delivery window for
    
    Returns:
        JSON string with delivery window details including dates, environment, and notes
    """
    window = _DELIVERY_WINDOWS.get(route_slug)
    if window is None:
        return json.dumps({"error": f"Delivery window for '{route_slug}' not found"})
    
    # Convert dates to ISO format for JSON serialization
    data = window.model_dump()
    data['window_start'] = data['window_start'].isoformat()
    data['window_end'] = data['window_end'].isoformat()
    return json.dumps(data, indent=2)


@tool
def fetch_support_contacts(audience_role: str) -> str:
    """Find support contacts and escalation channels for a specific audience role.
    
    Use this tool to identify:
    - Primary support contact emails
    - Escalation channels (Slack/Teams)
    - Role-specific support teams
    
    Args:
        audience_role: The role to find contacts for (e.g., 'Driver', 'Fleet Manager', 
                      'Dispatch Coordinator')
    
    Returns:
        JSON string with list of support contacts and their escalation channels
    """
    contacts = _SUPPORT_DIRECTORY.get(audience_role)
    if not contacts:
        contacts = [
            SupportContact(
                audience=audience_role,
                contact="support@logistics.example.com",
                escalation_channel="#general-support",
            )
        ]
    return json.dumps([c.model_dump() for c in contacts], indent=2)


@tool
def list_slo_watch_items(route_slug: str) -> str:
    """List critical SLO (Service Level Objective) items that need monitoring for a route.
    
    Use this tool to identify:
    - Performance metrics that must be tracked
    - Critical thresholds and requirements
    - Compliance and safety requirements
    
    Args:
        route_slug: The route identifier to get SLO items for
    
    Returns:
        JSON string with list of SLO items that require monitoring and attention
    """
    items = _SLO_WATCH_ITEMS.get(route_slug, [])
    return json.dumps({"route": route_slug, "slo_items": items}, indent=2)


@tool
def calculate_route_metrics(route_slug: str, distance_km: float, estimated_hours: float) -> str:
    """Calculate key performance metrics for a delivery route.
    
    Use this tool to compute:
    - Average speed (km/h)
    - Fuel efficiency estimates
    - Cost projections
    - Driver break requirements
    
    Args:
        route_slug: The route identifier
        distance_km: Total distance in kilometers
        estimated_hours: Estimated time in hours
    
    Returns:
        JSON string with calculated metrics and recommendations
    """
    if estimated_hours <= 0:
        return json.dumps({"error": "Estimated hours must be greater than 0"})
    
    avg_speed = distance_km / estimated_hours
    fuel_estimate = distance_km * 0.08  # 8L per 100km average
    cost_estimate = fuel_estimate * 1.5  # $1.50 per liter
    breaks_required = int(estimated_hours / 4)  # Break every 4 hours
    
    return json.dumps({
        "route": route_slug,
        "distance_km": distance_km,
        "estimated_hours": estimated_hours,
        "average_speed_kmh": round(avg_speed, 2),
        "fuel_estimate_liters": round(fuel_estimate, 2),
        "cost_estimate_usd": round(cost_estimate, 2),
        "driver_breaks_required": breaks_required,
        "recommendation": "Consider driver rest compliance" if breaks_required > 0 else "Short route, minimal breaks needed"
    }, indent=2)


@tool
def check_weather_impact(location: str, date_str: Optional[str] = None) -> str:
    """Check potential weather impacts on route planning.
    
    NOTE: This is a simulated tool. In production, integrate with a real weather API.
    
    Use this tool to assess:
    - Weather conditions for route planning
    - Potential delays or hazards
    - Recommendations for route adjustments
    
    Args:
        location: City or region name
        date_str: Optional date in YYYY-MM-DD format
    
    Returns:
        JSON string with weather assessment and recommendations
    """
    # Simulated weather data
    import random
    conditions = ["Clear", "Partly Cloudy", "Rain", "Heavy Rain", "Snow", "Fog"]
    condition = random.choice(conditions[:3])  # Bias toward good weather
    
    impact = "Low"
    recommendation = "Normal route operations expected"
    
    if condition in ["Rain", "Heavy Rain"]:
        impact = "Medium"
        recommendation = "Allow 15-20% additional travel time, ensure driver safety briefing"
    elif condition == "Snow":
        impact = "High"
        recommendation = "Consider route postponement or alternative routes, winter equipment required"
    
    return json.dumps({
        "location": location,
        "date": date_str or date.today().isoformat(),
        "condition": condition,
        "impact_level": impact,
        "recommendation": recommendation
    }, indent=2)


def list_slo_watch_items_direct(route_slug: str) -> list[str]:
    """Direct function access for internal use (not a LangChain tool)."""
    return _SLO_WATCH_ITEMS.get(route_slug, [])


# =============================================================================
# EXTERNAL TOOLS - Web Search, Wikipedia, etc.
# =============================================================================

def create_web_search_tools():
    """Create web search and research tools for the agent.
    
    These tools provide access to:
    - DuckDuckGo web search
    - Wikipedia lookup
    - ArXiv academic papers (for logistics research)
    
    Returns:
        List of initialized LangChain tools
    """
    from langchain_community.tools import DuckDuckGoSearchRun, WikipediaQueryRun
    from langchain_community.utilities import WikipediaAPIWrapper
    
    tools = []
    
    # DuckDuckGo Search
    try:
        search = DuckDuckGoSearchRun()
        tools.append(search)
    except Exception as e:
        print(f"Warning: Could not initialize DuckDuckGo search: {e}")
    
    # Wikipedia
    try:
        wikipedia = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())
        tools.append(wikipedia)
    except Exception as e:
        print(f"Warning: Could not initialize Wikipedia: {e}")
    
    return tools


def get_all_tools():
    """Get all available tools for the agent.
    
    This includes:
    - Internal logistics tools (route info, delivery windows, etc.)
    - External research tools (web search, Wikipedia)
    - Calculation tools (metrics, weather)
    
    Returns:
        List of all LangChain tools available to the agent
    """
    # Internal tools
    internal_tools = [
        fetch_route_brief,
        fetch_delivery_window,
        fetch_support_contacts,
        list_slo_watch_items,
        calculate_route_metrics,
        check_weather_impact,
    ]
    
    # External tools
    external_tools = create_web_search_tools()
    
    # Combine all tools
    all_tools = internal_tools + external_tools
    
    return all_tools


def list_slo_watch_items(route_slug: str) -> list[str]:
    """List performance and reliability signals for the route."""
    return _SLO_WATCH_ITEMS.get(route_slug, [])
