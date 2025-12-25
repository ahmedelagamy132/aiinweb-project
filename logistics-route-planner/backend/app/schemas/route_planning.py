"""Route planning schemas for AI agent."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class DeliveryStop(BaseModel):
    """A single delivery stop in a route."""
    
    stop_id: str = Field(..., description="Unique identifier for this stop")
    location: str = Field(..., description="Address or location description")
    sequence_number: int = Field(..., description="Current planned order in route")
    time_window_start: Optional[str] = Field(None, description="Earliest delivery time (HH:MM format)")
    time_window_end: Optional[str] = Field(None, description="Latest delivery time (HH:MM format)")
    priority: Literal["low", "normal", "high"] = Field(default="normal", description="Delivery priority level")
    service_time_minutes: Optional[int] = Field(None, description="Estimated service time at stop in minutes")
    latitude: Optional[float] = Field(None, description="Latitude of the stop location")
    longitude: Optional[float] = Field(None, description="Longitude of the stop location")


class OperationalConstraints(BaseModel):
    """Operational constraints for route planning."""
    
    max_route_duration_hours: Optional[float] = Field(None, description="Maximum hours for complete route")
    driver_shift_end: Optional[str] = Field(None, description="Driver shift end time (HH:MM format)")
    vehicle_capacity: Optional[float] = Field(None, description="Maximum vehicle capacity (weight/volume)")
    notes: Optional[str] = Field(None, description="Additional constraints or notes")


class RouteRequest(BaseModel):
    """Complete route planning request from dispatcher."""
    
    # Route metadata
    route_id: str = Field(..., description="Unique route identifier")
    start_location: str = Field(..., description="Depot or warehouse starting point")
    planned_start_time: str = Field(..., description="Planned start time (ISO8601 datetime string)")
    vehicle_id: Optional[str] = Field(None, description="Assigned vehicle identifier")
    vehicle_type: Optional[str] = Field("van", description="Vehicle type (van/truck/motorcycle) for metrics calculation")
    start_latitude: Optional[float] = Field(None, description="Latitude of the start location")
    start_longitude: Optional[float] = Field(None, description="Longitude of the start location")
    
    # Delivery stops
    stops: list[DeliveryStop] = Field(..., description="List of delivery stops in route")
    
    # Operational constraints
    constraints: Optional[OperationalConstraints] = Field(None, description="Route constraints")
    
    # Task instruction
    task: Literal["validate_route", "optimize_route", "validate_and_recommend"] = Field(
        ..., 
        description="What the agent should do with this route"
    )


class RouteValidationResult(BaseModel):
    """AI agent's route validation/optimization result."""
    
    is_valid: bool = Field(..., description="Whether the route is valid and feasible")
    issues: list[str] = Field(default_factory=list, description="List of problems found")
    recommendations: list[str] = Field(default_factory=list, description="Suggested improvements")
    action_plan: list[str] = Field(default_factory=list, description="Ordered step-by-step execution plan")
    optimized_stop_order: Optional[list[str]] = Field(None, description="Optimized sequence of stop_ids")
    summary: str = Field(..., description="Human-readable explanation of validation/optimization")
    estimated_duration_hours: Optional[float] = Field(None, description="Estimated total route duration")
    estimated_distance_km: Optional[float] = Field(None, description="Estimated total distance")
    tool_calls: Optional[list[dict[str, Any]]] = Field(None, description="List of AI tools used in analysis")
