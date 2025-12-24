"""Route plan generation and validation service."""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import RouteRun
from app.schemas.planner import (
    RouteAudience,
    RoutePlan,
    RouteRequest,
    RouteStep,
    RouteValidationResult,
)

try:
    import google.generativeai as genai
except ImportError:
    genai = None

try:
    from groq import Groq
except ImportError:
    Groq = None


def _generate_ai_plan(request: RouteRequest) -> RoutePlan | None:
    """Use LLM to generate route plan dynamically."""
    settings = get_settings()
    
    # Try Groq first
    if settings.groq_api_key and Groq is not None:
        try:
            client = Groq(api_key=settings.groq_api_key)
            model_name = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
            
            prompt = f"""You are a logistics route planning expert. Generate a detailed route plan with specific steps.

Request:
- Goal: {request.goal}
- Audience Role: {request.audience_role}
- Experience Level: {request.audience_experience}
- Primary Risk: {request.primary_risk or "None specified"}

Generate a JSON object with this EXACT structure:
{{
  "steps": [
    {{
      "title": "Step Title",
      "description": "Detailed description of what to do",
      "owner": "Role responsible",
      "duration_minutes": 30,
      "acceptance_criteria": ["Criterion 1", "Criterion 2"]
    }}
  ],
  "risks": ["Risk 1", "Risk 2", "Risk 3"]
}}

Generate 4-6 relevant steps appropriate for {request.audience_experience} experience level.
Include specific logistics steps like: route assessment, vehicle selection, optimization, driver briefing, customer notification, dispatch execution.
Make risks specific to the goal and primary risk mentioned.
Return ONLY the JSON, no other text."""

            completion = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_completion_tokens=2048,
            )
            
            response_text = completion.choices[0].message.content.strip()
            
            # Extract JSON if wrapped in markdown code blocks
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            import json
            plan_data = json.loads(response_text)
            
            # Build RoutePlan from LLM response
            steps = [RouteStep(**step) for step in plan_data["steps"]]
            risks = plan_data.get("risks", [])
            
            return RoutePlan(
                goal=request.goal,
                audience=RouteAudience(
                    role=request.audience_role,
                    experience_level=request.audience_experience,
                ),
                created_at=datetime.utcnow(),
                steps=steps,
                risks=risks,
            )
        except Exception as exc:
            print(f"Groq plan generation failed: {exc}")
    
    # Try Gemini fallback
    if settings.gemini_api_key and genai is not None:
        try:
            genai.configure(api_key=settings.gemini_api_key)
            model = genai.GenerativeModel(os.getenv("GEMINI_MODEL", "gemini-2.0-flash"))
            
            prompt = f"""You are a logistics route planning expert. Generate a detailed route plan with specific steps.

Request:
- Goal: {request.goal}
- Audience Role: {request.audience_role}
- Experience Level: {request.audience_experience}
- Primary Risk: {request.primary_risk or "None specified"}

Generate a JSON object with this EXACT structure:
{{
  "steps": [
    {{
      "title": "Step Title",
      "description": "Detailed description of what to do",
      "owner": "Role responsible",
      "duration_minutes": 30,
      "acceptance_criteria": ["Criterion 1", "Criterion 2"]
    }}
  ],
  "risks": ["Risk 1", "Risk 2", "Risk 3"]
}}

Generate 4-6 relevant steps appropriate for {request.audience_experience} experience level.
Include specific logistics steps like: route assessment, vehicle selection, optimization, driver briefing, customer notification, dispatch execution.
Make risks specific to the goal and primary risk mentioned.
Return ONLY the JSON, no other text."""

            response = model.generate_content(prompt)
            response_text = getattr(response, "text", "").strip()
            
            # Extract JSON if wrapped in markdown code blocks
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            import json
            plan_data = json.loads(response_text)
            
            # Build RoutePlan from LLM response
            steps = [RouteStep(**step) for step in plan_data["steps"]]
            risks = plan_data.get("risks", [])
            
            return RoutePlan(
                goal=request.goal,
                audience=RouteAudience(
                    role=request.audience_role,
                    experience_level=request.audience_experience,
                ),
                created_at=datetime.utcnow(),
                steps=steps,
                risks=risks,
            )
        except Exception as exc:
            print(f"Gemini plan generation failed: {exc}")
    
    return None


def build_route_plan(request: RouteRequest) -> RoutePlan:
    """Generate a structured route plan based on the request parameters.
    
    Now uses LLM (Groq/Gemini) for dynamic plan generation with fallback to rule-based templates.
    """
    
    # Try AI-based generation first
    ai_plan = _generate_ai_plan(request)
    if ai_plan:
        return ai_plan
    
    # Fallback to rule-based template generation if AI fails or unavailable
    print("⚠️ LLM unavailable, using rule-based fallback template")
    
    # Base steps for all experience levels
    steps = [
        RouteStep(
            title="Route Assessment",
            description="Analyze the delivery requirements, destinations, and time constraints for the route.",
            owner="Route Planner",
            duration_minutes=30,
            acceptance_criteria=[
                "All delivery addresses verified",
                "Time windows confirmed with customers",
            ],
        ),
        RouteStep(
            title="Vehicle Selection",
            description="Select appropriate vehicle based on cargo size, weight, and delivery requirements.",
            owner="Fleet Manager",
            duration_minutes=15,
            acceptance_criteria=[
                "Vehicle capacity matches cargo requirements",
                "Vehicle inspection completed",
            ],
        ),
        RouteStep(
            title="Route Optimization",
            description="Optimize the delivery sequence to minimize travel time and fuel consumption.",
            owner="Route Planner",
            duration_minutes=45,
            acceptance_criteria=[
                "Route sequence minimizes total distance",
                "Traffic patterns considered",
            ],
        ),
    ]

    # Add experience-specific steps
    if request.audience_experience == "beginner":
        steps.append(
            RouteStep(
                title="Driver Briefing",
                description="Provide detailed briefing to the driver including route maps, customer instructions, and safety protocols.",
                owner="Dispatch Coordinator",
                duration_minutes=30,
                acceptance_criteria=[
                    "Driver acknowledges route details",
                    "Safety checklist completed",
                ],
            )
        )
    elif request.audience_experience == "intermediate":
        steps.append(
            RouteStep(
                title="Customer Notification",
                description="Send delivery notifications to customers with estimated arrival times.",
                owner="Customer Service",
                duration_minutes=20,
                acceptance_criteria=[
                    "All customers notified",
                    "Special instructions documented",
                ],
            )
        )
    else:  # advanced
        steps.append(
            RouteStep(
                title="Performance Metrics Setup",
                description="Configure tracking and KPI monitoring for route efficiency analysis.",
                owner="Operations Analyst",
                duration_minutes=25,
                acceptance_criteria=[
                    "Real-time tracking enabled",
                    "Performance dashboards configured",
                ],
            )
        )

    # Add final step
    steps.append(
        RouteStep(
            title="Dispatch Execution",
            description="Execute the route dispatch and monitor progress throughout delivery operations.",
            owner="Dispatch Coordinator",
            duration_minutes=60,
            acceptance_criteria=[
                "Driver departed on schedule",
                "First delivery completed successfully",
            ],
        )
    )

    # Build risks list
    risks = []
    if request.primary_risk:
        risks.append(request.primary_risk)

    # Add common logistics risks
    risks.extend([
        "Traffic delays may impact delivery windows",
        "Vehicle breakdown could require backup dispatch",
    ])

    return RoutePlan(
        goal=request.goal,
        audience=RouteAudience(
            role=request.audience_role,
            experience_level=request.audience_experience,
        ),
        created_at=datetime.utcnow(),
        steps=steps,
        risks=risks,
    )


def validate_route_payload(payload: dict[str, Any]) -> RouteValidationResult:
    """Validate or repair arbitrary route plan JSON."""
    messages: list[str] = []
    repaired = False

    # Attempt to parse as RoutePlan
    try:
        plan = RoutePlan(**payload)
        return RouteValidationResult(plan=plan, repaired=False, messages=[])
    except Exception:
        pass

    # Try to repair common issues
    if "goal" not in payload:
        payload["goal"] = "Route optimization"
        messages.append("Added default goal")
        repaired = True

    if "audience" not in payload:
        payload["audience"] = {"role": "Driver", "experience_level": "intermediate"}
        messages.append("Added default audience")
        repaired = True

    if "steps" not in payload or not payload["steps"]:
        payload["steps"] = [
            {
                "title": "Initial Assessment",
                "description": "Assess the route requirements and constraints.",
                "owner": "Route Planner",
                "duration_minutes": 30,
                "acceptance_criteria": [],
            }
        ]
        messages.append("Added default step")
        repaired = True

    if "risks" not in payload:
        payload["risks"] = []

    try:
        plan = RoutePlan(**payload)
        return RouteValidationResult(plan=plan, repaired=repaired, messages=messages)
    except Exception as exc:
        raise ValueError(f"Unable to repair plan: {exc}") from exc


def save_route_run(db: Session, request: RouteRequest, plan: RoutePlan) -> RouteRun:
    """Persist a route plan run to the database."""
    summary = f"Route plan for {request.goal} targeting {request.audience_role} ({request.audience_experience})"

    run = RouteRun(
        goal=request.goal,
        audience_role=request.audience_role,
        audience_experience=request.audience_experience,
        primary_risk=request.primary_risk,
        include_risks=bool(request.primary_risk),
        summary=summary,
        plan=plan.model_dump(mode="json"),
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run
