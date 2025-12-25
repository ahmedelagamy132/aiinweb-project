"""LangChain-based route validation agent with real tools.

This module implements route validation using:
- Real tools: weather API, route calculations, optimization, traffic analysis
- LLM-powered validation and recommendations
- RAG integration for knowledge base access
"""

from __future__ import annotations

import json
import os
from typing import Any

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import AgentRun
from app.schemas.route_planning import RouteRequest, RouteValidationResult
from app.services.agent_tools import get_all_tools
from app.services.rag import RetrievedContext, build_retriever

# LLM imports
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
except ImportError:
    ChatGoogleGenerativeAI = None

try:
    from langchain_openai import ChatOpenAI
except ImportError:
    ChatOpenAI = None


class AgentServiceError(RuntimeError):
    """Raised when the agent cannot complete its workflow."""


class AgentToolCall(BaseModel):
    """Trace of a tool invocation the agent performed."""
    tool: str
    arguments: dict[str, Any]
    output: str  # Full output from the tool
    output_preview: str  # Truncated version for quick viewing


class RAGContext(BaseModel):
    """Retrieved context from the FAISS index."""
    content: str
    source: str
    score: float


def _safe_json_loads(value: Any) -> Any:
    """Safely load JSON content if the value is a JSON string."""
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except Exception:
            return None
    return None


def _format_metric(value: Any, suffix: str, precision: int = 2) -> str | None:
    """Format numeric metrics with consistent precision."""
    if isinstance(value, (int, float)):
        formatted = f"{value:.{precision}f}" if isinstance(value, float) else str(value)
        return f"{formatted}{suffix}"
    return None


def _build_structured_action_plan(
    route_request: RouteRequest,
    validation_result: RouteValidationResult,
    tool_payloads: dict[str, Any],
    resolved_locations: dict[str, str] | None = None
) -> list[str]:
    """Create a deterministic, data-backed execution plan for the dispatcher."""
    plan: list[str] = []

    # Resolve start location to city name if we have it
    start_display = route_request.start_location
    if resolved_locations and "start" in resolved_locations:
        start_display = f"{resolved_locations['start']} ({route_request.start_location})"

    stop_map = {stop.stop_id: stop for stop in route_request.stops}
    if validation_result.optimized_stop_order:
        ordered_stops = [stop_map.get(stop_id) for stop_id in validation_result.optimized_stop_order if stop_map.get(stop_id)]
    else:
        ordered_stops = sorted(route_request.stops, key=lambda s: s.sequence_number)

    if ordered_stops:
        route_segments = []
        for stop in ordered_stops:
            stop_display = stop.location
            if resolved_locations and stop.stop_id in resolved_locations:
                stop_display = f"{resolved_locations[stop.stop_id]} ({stop.location})"
            route_segments.append(f"{stop.stop_id} ({stop_display})")
        
        plan.append(
            f"Plot the delivery path on MapBox: start at {start_display} → "
            + " → ".join(route_segments)
        )

    metrics_data = tool_payloads.get("metrics") or {}
    if isinstance(metrics_data, dict) and metrics_data:
        metrics_parts: list[str] = []
        for key, suffix in (("distance_km", " km"), ("estimated_time_hours", " h"), ("fuel_consumption_liters", " L")):
            formatted = _format_metric(metrics_data.get(key), suffix)
            if formatted:
                metrics_parts.append(formatted)
        fuel_cost = metrics_data.get("estimated_fuel_cost_usd")
        if isinstance(fuel_cost, (int, float)):
            metrics_parts.append(f"${fuel_cost:.2f} fuel cost")
        co2 = metrics_data.get("co2_emissions_kg")
        if isinstance(co2, (int, float)):
            metrics_parts.append(f"{co2:.2f} kg CO₂")
        if metrics_parts:
            plan.append("Review MapBox metrics: " + ", ".join(metrics_parts))

    weather_data = tool_payloads.get("weather") or {}
    if isinstance(weather_data, dict) and weather_data:
        cond = weather_data.get("current_conditions") or weather_data.get("conditions")
        temp = weather_data.get("temperature_celsius")
        wind = weather_data.get("wind_speed_mph")
        impact = weather_data.get("delivery_impact")
        weather_parts = []
        if cond:
            weather_parts.append(cond)
        if isinstance(temp, (int, float)):
            weather_parts.append(f"{temp:.1f}°C")
        if isinstance(wind, (int, float)):
            weather_parts.append(f"wind {wind:.1f} mph")
        impact_text = f" Impact: {impact}" if impact else ""
        if weather_parts or impact_text:
            plan.append(
                f"Brief the driver on conditions near {route_request.start_location}: "
                + ", ".join(weather_parts)
                + impact_text
            )

    traffic_data = tool_payloads.get("traffic") or {}
    if isinstance(traffic_data, dict) and traffic_data:
        level = traffic_data.get("traffic_level")
        delay_factor = traffic_data.get("delay_factor")
        delay_minutes = traffic_data.get("delay_minutes") or traffic_data.get("estimated_delay_minutes")
        traffic_parts = []
        if level:
            traffic_parts.append(level)
        if isinstance(delay_factor, (int, float)):
            traffic_parts.append(f"delay factor {delay_factor:.2f}x")
        if isinstance(delay_minutes, (int, float)) and delay_minutes > 0:
            traffic_parts.append(f"~{delay_minutes:.1f} min extra")
        if traffic_parts:
            plan.append("Incorporate MapBox traffic insights: " + ", ".join(traffic_parts))

    timing_data = tool_payloads.get("timing_validation") or {}
    constraints = route_request.constraints
    if isinstance(timing_data, dict) or constraints is not None:
        timing_parts: list[str] = []
        if isinstance(timing_data, dict):
            if not timing_data.get("is_valid", True):
                issues = timing_data.get("issues") or []
                if issues:
                    timing_parts.append(f"resolve timing issues ({'; '.join(issues[:2])})")
        if constraints:
            constraint_bits = []
            if constraints.max_route_duration_hours is not None:
                constraint_bits.append(f"max {constraints.max_route_duration_hours} h")
            if constraints.driver_shift_end:
                constraint_bits.append(f"shift end {constraints.driver_shift_end}")
            if constraints.vehicle_capacity is not None:
                constraint_bits.append(f"capacity {constraints.vehicle_capacity}")
            if constraint_bits:
                timing_parts.append("respect constraints: " + ", ".join(constraint_bits))
        if timing_parts:
            plan.append("Confirm schedule alignment: " + "; ".join(timing_parts))

    if ordered_stops:
        plan.append("Dispatch, follow the plotted sequence, and capture completion updates after each stop.")

    return [step for step in plan if step]


def _get_llm():
    """Get the configured LLM (Gemini or Groq via OpenAI compatibility)."""
    settings = get_settings()
    
    # Try Gemini first
    if settings.gemini_api_key and ChatGoogleGenerativeAI:
        return ChatGoogleGenerativeAI(
            model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
            google_api_key=settings.gemini_api_key,
            temperature=0.7,
        )
    
    # Try Groq (via OpenAI-compatible API)
    if settings.groq_api_key and ChatOpenAI:
        return ChatOpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=settings.groq_api_key,
            model=os.getenv("GROQ_MODEL", "llama3-8b-8192"),
            temperature=0.7,
        )
    
    raise AgentServiceError("No LLM provider configured (need GEMINI_API_KEY or GROQ_API_KEY)")


def run_route_validation_agent(
    route_request: RouteRequest,
    db: Session | None = None,
) -> RouteValidationResult:
    """Run LangChain agent with real route planning tools.
    
    This implementation:
    1. Uses real tools: weather API, route calculations, optimization, traffic analysis
    2. Validates route feasibility based on time windows and constraints
    3. Provides optimization recommendations
    4. Returns structured validation result
    """
    
    # Get LLM
    llm = _get_llm()
    
    # Resolve coordinates to city names for display
    from app.services.agent_tools import reverse_geocode_mapbox
    resolved_locations: dict[str, str] = {}
    
    # Resolve start location if it has coordinates
    if hasattr(route_request, 'start_latitude') and hasattr(route_request, 'start_longitude'):
        if route_request.start_latitude and route_request.start_longitude:
            geo_result = reverse_geocode_mapbox(route_request.start_latitude, route_request.start_longitude)
            if geo_result:
                resolved_locations["start"] = geo_result.get("formatted", geo_result.get("city", ""))
    
    # Resolve stop locations if they have coordinates
    for stop in route_request.stops:
        if hasattr(stop, 'latitude') and hasattr(stop, 'longitude'):
            if stop.latitude and stop.longitude:
                geo_result = reverse_geocode_mapbox(stop.latitude, stop.longitude)
                if geo_result:
                    resolved_locations[stop.stop_id] = geo_result.get("formatted", geo_result.get("city", ""))
    
    # Get all available real tools
    tools = get_all_tools()
    
    # Create RAG context
    rag_contexts: list[RetrievedContext] = []
    if db is not None:
        retriever = build_retriever(db)
        search_query = f"route planning delivery logistics {route_request.task}"
        rag_contexts = retriever.search(search_query, k=3)
    
    # Execute real tools based on task
    try:
        tool_calls = []
        tool_results = {}
        
        # Tool 1: Check weather for start location
        from app.services.agent_tools import check_weather_conditions
        try:
            weather_result = check_weather_conditions.invoke({"location": route_request.start_location})
            tool_calls.append(
                AgentToolCall(
                    tool="check_weather_conditions",
                    arguments={"location": route_request.start_location},
                    output=weather_result,
                    output_preview=weather_result[:200] + "..." if len(weather_result) > 200 else weather_result,
                )
            )
            tool_results['weather'] = weather_result
            print(f"[TOOL] Weather result: {weather_result[:500]}")
        except Exception as e:
            tool_results['weather'] = f"Weather unavailable: {e}"
            print(f"[TOOL ERROR] Weather failed: {e}")
        
        # Tool 2: Calculate route metrics
        if len(route_request.stops) > 0:
            from app.services.agent_tools import calculate_route_metrics
            try:
                # Calculate actual distance using geopy
                from geopy.distance import geodesic
                import re
                
                def extract_coords(location_str):
                    """Extract coordinates from location string or return approximate coords."""
                    # Try to extract lat/lng if present in the string
                    match = re.search(r'(-?\d+\.\d+),\s*(-?\d+\.\d+)', location_str)
                    if match:
                        return (float(match.group(1)), float(match.group(2)))
                    # For demo: return None and use default estimate
                    return None
                
                total_distance_km = 0
                start_coords = extract_coords(route_request.start_location)
                
                # Calculate cumulative distance between consecutive stops
                prev_location = route_request.start_location
                for stop in route_request.stops:
                    # Use geodesic if coordinates available, otherwise estimate
                    curr_coords = extract_coords(stop.location)
                    if start_coords and curr_coords:
                        # Use actual distance calculation
                        distance = geodesic(start_coords, curr_coords).kilometers
                        total_distance_km += distance
                        start_coords = curr_coords
                    else:
                        # Fallback: estimate based on urban delivery patterns (5-20km per stop)
                        import random
                        random.seed(hash(stop.location))  # Consistent per location
                        total_distance_km += random.uniform(8, 18)
                
                route_data = {
                    "start_location": route_request.start_location,
                    "start_latitude": getattr(route_request, "start_latitude", None),
                    "start_longitude": getattr(route_request, "start_longitude", None),
                    "stops": [
                        {
                            "location": stop.location,
                            "latitude": getattr(stop, "latitude", None),
                            "longitude": getattr(stop, "longitude", None),
                        }
                        for stop in route_request.stops
                    ],
                    "area_type": "urban",
                    "vehicle_type": route_request.vehicle_type or "van"
                }
                print(f"[TOOL] Calling calculate_route_metrics with: {route_data}")
                metrics_result = calculate_route_metrics.invoke({"route_data": route_data})
                tool_calls.append(
                    AgentToolCall(
                        tool="calculate_route_metrics",
                        arguments=route_data,
                        output=metrics_result,  # Full output
                        output_preview=metrics_result[:200] + "..." if len(metrics_result) > 200 else metrics_result,
                    )
                )
                tool_results['metrics'] = metrics_result
                print(f"[TOOL] Metrics result: {metrics_result[:500]}")
            except Exception as e:
                tool_results['metrics'] = f"Calculation error: {e}"
                print(f"[TOOL ERROR] Metrics failed: {e}")
        
        # Tool 3: Validate route timing (if task includes validation)
        if route_request.task in ["validate_route", "validate_and_recommend"]:
            from app.services.agent_tools import validate_route_timing
            try:
                route_data_for_validation = route_request.model_dump()
                print(f"[TOOL] Calling validate_route_timing with: {json.dumps(route_data_for_validation, indent=2)}")
                timing_result = validate_route_timing.invoke({"route_request": route_data_for_validation})
                tool_calls.append(
                    AgentToolCall(
                        tool="validate_route_timing",
                        arguments={"route_id": route_request.route_id},
                        output=timing_result,
                        output_preview=timing_result[:200] + "..." if len(timing_result) > 200 else timing_result,
                    )
                )
                tool_results['timing_validation'] = timing_result
                print(f"[TOOL] Timing validation result: {timing_result[:500]}")
            except Exception as e:
                tool_results['timing_validation'] = f"Validation error: {e}"
                print(f"[TOOL ERROR] Timing validation failed: {e}")
        
        # Tool 4: Optimize stop sequence (if task includes optimization)
        if route_request.task in ["optimize_route", "validate_and_recommend"]:
            from app.services.agent_tools import optimize_stop_sequence
            try:
                route_data_for_optimization = route_request.model_dump()
                optimization_result = optimize_stop_sequence.invoke({"route_request": route_data_for_optimization})
                tool_calls.append(
                    AgentToolCall(
                        tool="optimize_stop_sequence",
                        arguments={"route_id": route_request.route_id},
                        output=optimization_result,
                        output_preview=optimization_result[:200] + "..." if len(optimization_result) > 200 else optimization_result,
                    )
                )
                tool_results['optimization'] = optimization_result
            except Exception as e:
                tool_results['optimization'] = f"Optimization error: {e}"
        
        # Tool 5: Check traffic conditions for each stop location
        from app.services.agent_tools import check_traffic_conditions
        from datetime import datetime
        try:
            # Parse planned_start_time to get time of day
            start_dt = datetime.fromisoformat(route_request.planned_start_time.replace('Z', '+00:00'))
            time_of_day = start_dt.strftime("%H:%M")
            
            traffic_result = check_traffic_conditions.invoke({
                "location": route_request.start_location,
                "time_of_day": time_of_day
            })
            tool_calls.append(
                AgentToolCall(
                    tool="check_traffic_conditions",
                    arguments={"location": route_request.start_location, "time_of_day": time_of_day},
                    output=traffic_result,
                    output_preview=traffic_result[:200] + "..." if len(traffic_result) > 200 else traffic_result,
                )
            )
            tool_results['traffic'] = traffic_result
        except Exception as e:
            tool_results['traffic'] = f"Traffic check unavailable: {e}"
        
        # Add RAG context if available
        if rag_contexts:
            tool_calls.append(
                AgentToolCall(
                    tool="rag_retrieval",
                    arguments={"query": "route planning best practices", "k": 3},
                    output=json.dumps({"document_count": len(rag_contexts), "status": "success"}),
                    output_preview=f"Retrieved {len(rag_contexts)} relevant documents",
                )
            )
        
        # Build context from tool results for LLM
        tool_context = "\n\n".join([
            f"=== {key.upper()} ===\n{value}"
            for key, value in tool_results.items()
        ])

        if rag_contexts:
            rag_text = "\n".join([f"- ({ctx.source}) {ctx.content[:200]}..." for ctx in rag_contexts])
            tool_context += f"\n\n=== KNOWLEDGE BASE ===\n{rag_text}"

        # Build detailed stop snapshot for the LLM
        stop_summaries = []
        for stop in route_request.stops:
            window = f"{stop.time_window_start or '—'} to {stop.time_window_end or '—'}"
            coords = f"lat={getattr(stop, 'latitude', None)}, lon={getattr(stop, 'longitude', None)}"
            
            # Add city name if resolved
            location_display = stop.location
            if resolved_locations.get(stop.stop_id):
                location_display = f"{resolved_locations[stop.stop_id]} ({stop.location})"
            
            stop_summaries.append(
                f"{stop.stop_id}: {location_display} | seq={stop.sequence_number} | priority={stop.priority} | window={window} | {coords}"
            )
        stops_detail = "\n".join(stop_summaries) if stop_summaries else "No stops supplied"

        # Create prompt for route validation
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert logistics route validation AI with access to reliable tool outputs (weather, traffic, metrics, timing, optimization).

    Use the provided data to evaluate the route's feasibility and recommend improvements. When you cite specifics, pull exact numbers from the tool outputs.

    Respond strictly in this format (omit lines that do not apply):
    VALID: true/false
    ISSUE: <specific problem>
    RECOMMENDATION: <actionable suggestion>
    OPTIMIZED_ORDER: stop_id1,stop_id2,stop_id3
    SUMMARY: <brief human-readable explanation>"""),
            ("human", """Tool Results:
{tool_context}

Route Overview:
- Route ID: {route_id}
- Start: {start_location} at {planned_start_time}
- Vehicle: {vehicle_id}
- Task: {task}
- Constraints: {constraints}

Stops Detail:
{stops_detail}

    Provide your validation and recommendations based on these facts.""")
        ])
        
        # Invoke LLM
        chain = prompt | llm
        
        # Format start location with city name if available
        start_location_display = route_request.start_location
        if resolved_locations.get("start"):
            start_location_display = f"{resolved_locations['start']} ({route_request.start_location})"
        
        response = chain.invoke({
            "tool_context": tool_context,
            "route_id": route_request.route_id,
            "start_location": start_location_display,
            "planned_start_time": route_request.planned_start_time,
            "vehicle_id": route_request.vehicle_id or "unassigned",
            "task": route_request.task,
            "constraints": json.dumps(route_request.constraints.model_dump() if route_request.constraints else {}),
            "stops_detail": stops_detail,
        })
        
        # Extract text content from response
        if hasattr(response, "content"):
            agent_output = response.content
        else:
            agent_output = str(response)
        
        # Log agent output for debugging
        print(f"=== AGENT OUTPUT ===\n{agent_output}\n=== END AGENT OUTPUT ===")
        
        # Parse validation result from agent output
        validation_result = _parse_validation_result(
            agent_output, 
            route_request, 
            tool_results,
            tool_calls=[tc.model_dump() for tc in tool_calls]
        )

        parsed_payloads = {
            "weather": _safe_json_loads(tool_results.get("weather")),
            "metrics": _safe_json_loads(tool_results.get("metrics")),
            "traffic": _safe_json_loads(tool_results.get("traffic")),
            "timing_validation": _safe_json_loads(tool_results.get("timing_validation")),
            "optimization": _safe_json_loads(tool_results.get("optimization")),
        }

        validation_result.action_plan = _build_structured_action_plan(
            route_request,
            validation_result,
            parsed_payloads,
            resolved_locations,
        )
        
        # Persist to database
        if db is not None:
            rag_context_response = [
                RAGContext(content=ctx.content, source=ctx.source, score=ctx.score)
                for ctx in rag_contexts
            ]
            
            recommended_actions_payload = [
                {"title": f"Step {idx + 1}", "detail": step, "priority": "high"}
                for idx, step in enumerate(validation_result.action_plan)
            ] + [
                {"title": rec, "detail": rec, "priority": "medium"}
                for rec in validation_result.recommendations
            ]

            agent_run = AgentRun(
                route_slug=route_request.route_id,
                audience_role="dispatcher",
                audience_experience="advanced",
                summary=validation_result.summary,
                gemini_insight=agent_output,
                recommended_actions=recommended_actions_payload,
                tool_calls=[tc.model_dump() for tc in tool_calls],
                rag_contexts=[ctx.model_dump() for ctx in rag_context_response],
                used_gemini=True,
            )
            db.add(agent_run)
            db.commit()
        
        return validation_result
        
    except Exception as exc:
        print(f"Agent execution error: {exc}")
        import traceback
        traceback.print_exc()
        raise AgentServiceError(f"Agent execution failed: {exc}") from exc


def _parse_validation_result(agent_output: str, route_request: RouteRequest, tool_results: dict, tool_calls: list = None) -> RouteValidationResult:
    """Parse agent output to extract validation result."""
    
    is_valid = True
    issues = []
    recommendations = []
    action_plan: list[str] = []
    optimized_stop_order = None
    summary = ""
    estimated_duration_hours = None
    estimated_distance_km = None
    
    # Parse structured output
    lines = agent_output.split("\n")
    for line in lines:
        line = line.strip()
        if line.startswith("VALID:"):
            is_valid = "true" in line.lower()
        elif line.startswith("ISSUE:"):
            issue_text = line.replace("ISSUE:", "").strip()
            if issue_text:
                issues.append(issue_text)
        elif line.startswith("RECOMMENDATION:"):
            rec_text = line.replace("RECOMMENDATION:", "").strip()
            if rec_text:
                recommendations.append(rec_text)
        elif line.startswith("OPTIMIZED_ORDER:"):
            order_text = line.replace("OPTIMIZED_ORDER:", "").strip()
            if order_text:
                optimized_stop_order = [s.strip() for s in order_text.split(",")]
        elif line.startswith("SUMMARY:"):
            summary = line.replace("SUMMARY:", "").strip()
    
    # Extract data from tool results
    if 'timing_validation' in tool_results:
        try:
            timing_data = json.loads(tool_results['timing_validation'])
            if not timing_data.get('is_valid', True):
                is_valid = False
                issues.extend(timing_data.get('issues', []))
        except:
            pass
    
    if 'metrics' in tool_results:
        try:
            metrics_data = json.loads(tool_results['metrics'])
            estimated_duration_hours = metrics_data.get('estimated_time_hours')
            estimated_distance_km = metrics_data.get('distance_km')
        except:
            pass
    
    if 'optimization' in tool_results and not optimized_stop_order:
        try:
            opt_data = json.loads(tool_results['optimization'])
            optimized_stop_order = opt_data.get('optimized_sequence', [])
        except:
            pass
    
    # Generate default summary if not provided
    if not summary:
        if is_valid:
            summary = f"Route {route_request.route_id} is valid with {len(route_request.stops)} stops. " + \
                     (f"Estimated duration: {estimated_duration_hours:.1f}h. " if estimated_duration_hours else "") + \
                     f"{len(recommendations)} recommendations provided."
        else:
            summary = f"Route {route_request.route_id} has {len(issues)} issues that must be addressed before execution."
    
    return RouteValidationResult(
        is_valid=is_valid,
        issues=issues,
        recommendations=recommendations,
        action_plan=action_plan,
        optimized_stop_order=optimized_stop_order,
        summary=summary,
        estimated_duration_hours=estimated_duration_hours,
        estimated_distance_km=estimated_distance_km,
        tool_calls=tool_calls or []
    )


def get_agent_history(db: Session, route_slug: str | None = None, limit: int = 10) -> list[AgentRun]:
    """Retrieve historical agent runs from the database."""
    from sqlalchemy import select

    query = select(AgentRun).order_by(AgentRun.created_at.desc()).limit(limit)
    if route_slug:
        query = query.where(AgentRun.route_slug == route_slug)
    return list(db.execute(query).scalars().all())
