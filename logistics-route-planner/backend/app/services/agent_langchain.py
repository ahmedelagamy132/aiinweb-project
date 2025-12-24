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
    output_preview: str


class RAGContext(BaseModel):
    """Retrieved context from the FAISS index."""
    content: str
    source: str
    score: float


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
                route_data = {
                    "distance_km": len(route_request.stops) * 15,  # Estimate 15km per stop
                    "stops": len(route_request.stops),
                    "area_type": "urban",  # Could be inferred from location
                    "vehicle_type": "van"  # Could come from vehicle_id lookup
                }
                print(f"[TOOL] Calling calculate_route_metrics with: {route_data}")
                metrics_result = calculate_route_metrics.invoke({"route_data": route_data})
                tool_calls.append(
                    AgentToolCall(
                        tool="calculate_route_metrics",
                        arguments=route_data,
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
        
        # Create prompt for route validation
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert logistics route validation AI.

Based on the tool results below, analyze the route and provide:
1. Whether the route is VALID (can be executed successfully) or INVALID
2. List of specific ISSUES found (timing problems, constraint violations, weather risks)
3. List of RECOMMENDATIONS for improvement
4. If optimization was requested, provide the optimized stop order

Respond in this format:
VALID: true/false
ISSUE: <specific problem>
ISSUE: <specific problem>
RECOMMENDATION: <actionable suggestion>
RECOMMENDATION: <actionable suggestion>
OPTIMIZED_ORDER: stop_id1,stop_id2,stop_id3
SUMMARY: <brief human-readable explanation>"""),
            ("human", """Tool Results:
{tool_context}

Route Request:
- Route ID: {route_id}
- Start: {start_location} at {planned_start_time}
- Vehicle: {vehicle_id}
- Stops: {num_stops} deliveries
- Task: {task}
- Constraints: {constraints}

Please validate this route.""")
        ])
        
        # Invoke LLM
        chain = prompt | llm
        response = chain.invoke({
            "tool_context": tool_context,
            "route_id": route_request.route_id,
            "start_location": route_request.start_location,
            "planned_start_time": route_request.planned_start_time,
            "vehicle_id": route_request.vehicle_id or "unassigned",
            "num_stops": len(route_request.stops),
            "task": route_request.task,
            "constraints": json.dumps(route_request.constraints.model_dump() if route_request.constraints else {}),
        })
        
        # Extract text content from response
        if hasattr(response, "content"):
            agent_output = response.content
        else:
            agent_output = str(response)
        
        # Parse validation result from agent output
        validation_result = _parse_validation_result(agent_output, route_request, tool_results)
        
        # Persist to database
        if db is not None:
            rag_context_response = [
                RAGContext(content=ctx.content, source=ctx.source, score=ctx.score)
                for ctx in rag_contexts
            ]
            
            agent_run = AgentRun(
                route_slug=route_request.route_id,
                audience_role="dispatcher",
                audience_experience="advanced",
                summary=validation_result.summary,
                gemini_insight=agent_output,
                recommended_actions=[{"title": rec, "detail": rec, "priority": "medium"} for rec in validation_result.recommendations],
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


def _parse_validation_result(agent_output: str, route_request: RouteRequest, tool_results: dict) -> RouteValidationResult:
    """Parse agent output to extract validation result."""
    
    is_valid = True
    issues = []
    recommendations = []
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
            estimated_duration_hours = metrics_data.get('driving_time_hours')
            estimated_distance_km = metrics_data.get('distance_km')
        except:
            pass
    
    if 'optimization' in tool_results and not optimized_stop_order:
        try:
            opt_data = json.loads(tool_results['optimization'])
            optimized_stop_order = opt_data.get('optimized_stop_order', [])
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
        optimized_stop_order=optimized_stop_order,
        summary=summary,
        estimated_duration_hours=estimated_duration_hours,
        estimated_distance_km=estimated_distance_km,
    )


def get_agent_history(db: Session, route_slug: str | None = None, limit: int = 10) -> list[AgentRun]:
    """Retrieve historical agent runs from the database."""
    from sqlalchemy import select

    query = select(AgentRun).order_by(AgentRun.created_at.desc()).limit(limit)
    if route_slug:
        query = query.where(AgentRun.route_slug == route_slug)
    return list(db.execute(query).scalars().all())
