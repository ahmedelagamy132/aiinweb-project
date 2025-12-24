"""LangChain-based agent service with real tools and AgentExecutor.

This module implements a powerful AI agent using:
- Real LangChain tools (not just function calls)
- AgentExecutor for autonomous tool usage
- Multiple tool types: internal logistics tools + external research tools
- RAG integration for knowledge base access
"""

from __future__ import annotations

import os
from datetime import date
from typing import Any, Literal

from langchain_core.prompts import ChatPromptTemplate
from langchain.agents import AgentExecutor, create_tool_calling_agent
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import AgentRun
from app.schemas.planner import RoutePlan, RouteRequest
from app.services.agent_tools import get_all_tools, list_slo_watch_items_direct, _ROUTE_BRIEFS
from app.services.planner import build_route_plan
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


class AgentRecommendation(BaseModel):
    """Action item recommended by the agent."""
    title: str
    detail: str
    priority: Literal["high", "medium", "low"] = "medium"


class RAGContext(BaseModel):
    """Retrieved context from the FAISS index."""
    content: str
    source: str
    score: float


class AgentRunContext(BaseModel):
    """Input payload submitted by the frontend."""
    route_slug: str = Field(..., min_length=2, max_length=40)
    launch_date: date
    audience_role: str = Field(..., min_length=2, max_length=60)
    audience_experience: Literal["beginner", "intermediate", "advanced"]
    include_risks: bool = Field(default=True)


class AgentRunResult(BaseModel):
    """Structured result returned to the frontend."""
    summary: str
    gemini_insight: str | None = None
    recommended_actions: list[AgentRecommendation]
    plan: RoutePlan
    tool_calls: list[AgentToolCall]
    rag_contexts: list[RAGContext] = []
    used_gemini: bool = False


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


def run_route_readiness_agent(
    context: AgentRunContext,
    db: Session | None = None,
) -> AgentRunResult:
    """Run LangChain agent with real tools and AgentExecutor.
    
    This implementation:
    1. Creates an agent with access to multiple tools
    2. Uses AgentExecutor to autonomously decide which tools to use
    3. Integrates RAG for knowledge base retrieval
    4. Generates structured recommendations
    """
    
    # Get LLM
    llm = _get_llm()
    
    # Get all available tools
    tools = get_all_tools()
    
    # Create RAG context first
    rag_contexts: list[RetrievedContext] = []
    rag_context_str = ""
    
    if db is not None:
        retriever = build_retriever(db)
        brief = _ROUTE_BRIEFS.get(context.route_slug)
        if brief:
            search_query = f"{brief.name} {context.audience_role} delivery logistics"
            rag_contexts = retriever.search(search_query, k=3)
            if rag_contexts:
                rag_context_str = "\n\nRelevant Documentation:\n" + "\n".join([
                    f"- ({ctx.source}) {ctx.content[:200]}..."
                    for ctx in rag_contexts
                ])
    
    # Create agent prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert logistics route readiness advisor helping teams prepare for route launches.

You have access to multiple tools that provide information about:
- Route details and specifications
- Delivery windows and timelines
- Support contacts and escalation channels
- SLO (Service Level Objectives) requirements
- Route metrics calculations
- Weather impact assessments
- Web search for latest logistics best practices
- Wikipedia for logistics concepts

Your task is to:
1. Gather comprehensive information about the route using available tools
2. Assess readiness for the launch date
3. Identify risks and provide actionable recommendations
4. Consider the audience's role and experience level

Use the tools autonomously to gather all necessary information. Start by fetching route brief and delivery window.
{rag_context}

After gathering information, provide:
- A strategic insight about route readiness
- Specific, actionable recommendations with priorities"""),
        ("human", """Please assess route readiness for:
- Route: {route_slug}
- Launch Date: {launch_date}
- Audience Role: {audience_role} ({audience_experience} level)
- Include Risk Analysis: {include_risks}

Use your tools to gather comprehensive information and provide a detailed assessment."""),
        ("placeholder", "{agent_scratchpad}"),
    ])
    
    # Create agent
    try:
        agent = create_tool_calling_agent(llm, tools, prompt)
        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            max_iterations=15,
            handle_parsing_errors=True,
            return_intermediate_steps=True,
        )
        
        # Execute agent
        result = agent_executor.invoke({
            "route_slug": context.route_slug,
            "launch_date": context.launch_date,
            "audience_role": context.audience_role,
            "audience_experience": context.audience_experience,
            "include_risks": context.include_risks,
            "rag_context": rag_context_str,
        })
        
        # Extract output and tool calls
        agent_output = result.get("output", "")
        intermediate_steps = result.get("intermediate_steps", [])
        
        # Build tool calls trace
        tool_calls = []
        for step in intermediate_steps:
            if len(step) >= 2:
                action, observation = step[0], step[1]
                tool_calls.append(
                    AgentToolCall(
                        tool=action.tool if hasattr(action, 'tool') else str(action),
                        arguments=action.tool_input if hasattr(action, 'tool_input') else {},
                        output_preview=str(observation)[:200] + "..." if len(str(observation)) > 200 else str(observation),
                    )
                )
        
        # Add RAG tool call
        if rag_contexts:
            tool_calls.append(
                AgentToolCall(
                    tool="rag_retrieval",
                    arguments={"query": search_query, "k": 3},
                    output_preview=f"Retrieved {len(rag_contexts)} relevant documents",
                )
            )
        
        # Parse agent output for recommendations
        recommendations = _parse_recommendations(agent_output, context)
        
        # Build summary
        brief = _ROUTE_BRIEFS.get(context.route_slug)
        if brief:
            summary = (
                f"{brief.name} targets {brief.audience_role} personas. "
                f"Launch date: {context.launch_date}. "
                f"Agent used {len(tool_calls)} tools for assessment."
            )
        else:
            summary = f"Route readiness assessment completed using {len(tool_calls)} tools."
        
        # Generate plan using planner service
        plan_request = RouteRequest(
            goal=f"Launch {context.route_slug} successfully",
            audience_role=context.audience_role,
            audience_experience=context.audience_experience,
            primary_risk=None,
        )
        plan = build_route_plan(plan_request)
        
        # Convert RAG contexts
        rag_context_response = [
            RAGContext(content=ctx.content, source=ctx.source, score=ctx.score)
            for ctx in rag_contexts
        ]
        
        agent_result = AgentRunResult(
            summary=summary,
            gemini_insight=agent_output,
            recommended_actions=recommendations,
            plan=plan,
            tool_calls=tool_calls,
            rag_contexts=rag_context_response,
            used_gemini=True,
        )
        
        # Persist to database
        if db is not None:
            agent_run = AgentRun(
                route_slug=context.route_slug,
                audience_role=context.audience_role,
                audience_experience=context.audience_experience,
                summary=summary,
                gemini_insight=agent_output,
                recommended_actions=[rec.model_dump() for rec in recommendations],
                tool_calls=[tc.model_dump() for tc in tool_calls],
                rag_contexts=[ctx.model_dump() for ctx in rag_context_response],
                used_gemini=True,
            )
            db.add(agent_run)
            db.commit()
        
        return agent_result
        
    except Exception as exc:
        print(f"Agent execution error: {exc}")
        import traceback
        traceback.print_exc()
        raise AgentServiceError(f"Agent execution failed: {exc}") from exc


def _parse_recommendations(agent_output: str, context: AgentRunContext) -> list[AgentRecommendation]:
    """Parse agent output to extract recommendations."""
    recommendations = []
    
    # Try to parse structured output
    lines = agent_output.split("\n")
    for line in lines:
        line = line.strip()
        if line.startswith("RECOMMENDATION:") or line.startswith("-"):
            # Extract recommendation from line
            text = line.replace("RECOMMENDATION:", "").replace("-", "").strip()
            if len(text) > 10:  # Valid recommendation
                # Try to parse priority
                priority = "medium"
                if "high" in text.lower() or "critical" in text.lower() or "urgent" in text.lower():
                    priority = "high"
                elif "low" in text.lower():
                    priority = "low"
                
                recommendations.append(
                    AgentRecommendation(
                        title=f"[AI Agent] {text[:60]}",
                        detail=text,
                        priority=priority,
                    )
                )
    
    # If no structured recommendations found, create from output
    if not recommendations and agent_output:
        # Split into sentences and create recommendations from meaningful ones
        sentences = [s.strip() for s in agent_output.split(".") if len(s.strip()) > 20]
        for i, sentence in enumerate(sentences[:3]):  # Max 3 recommendations
            if sentence and not sentence.startswith("Route:"):
                recommendations.append(
                    AgentRecommendation(
                        title=f"[AI Agent] Recommendation {i+1}",
                        detail=sentence + ".",
                        priority="medium",
                    )
                )
    
    # Add deterministic recommendation
    if len(recommendations) < 3:
        slo_items = list_slo_watch_items_direct(context.route_slug)
        if context.include_risks and slo_items:
            recommendations.append(
                AgentRecommendation(
                    title="Monitor Critical SLO",
                    detail=f"Create monitoring dashboard for: {slo_items[0]}",
                    priority="high",
                )
            )
    
    return recommendations[:5]  # Limit to 5 recommendations


def get_agent_history(db: Session, route_slug: str | None = None, limit: int = 10) -> list[AgentRun]:
    """Retrieve historical agent runs from the database."""
    from sqlalchemy import select

    query = select(AgentRun).order_by(AgentRun.created_at.desc()).limit(limit)
    if route_slug:
        query = query.where(AgentRun.route_slug == route_slug)
    return list(db.execute(query).scalars().all())
