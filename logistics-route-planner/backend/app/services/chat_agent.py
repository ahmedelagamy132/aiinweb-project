"""Chat agent service for flexible route planning queries."""

from __future__ import annotations

import json
import os
from typing import Any

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import get_settings
from app.services.agent_tools import get_all_tools
from app.services.rag import build_retriever

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
except ImportError:
    ChatGoogleGenerativeAI = None

try:
    from langchain_openai import ChatOpenAI
except ImportError:
    ChatOpenAI = None


class ToolCall(BaseModel):
    """Tool execution record."""
    tool: str
    arguments: dict[str, Any]
    output: str


class RAGContext(BaseModel):
    """Retrieved context from knowledge base."""
    content: str
    source: str
    score: float


class ChatResponse(BaseModel):
    """Response from chat agent."""
    answer: str
    tool_calls: list[ToolCall] = []
    rag_contexts: list[RAGContext] = []


def _get_llm():
    """Get configured LLM (Gemini or Groq)."""
    settings = get_settings()
    
    # Try Gemini first
    if settings.gemini_api_key and ChatGoogleGenerativeAI:
        return ChatGoogleGenerativeAI(
            model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
            google_api_key=settings.gemini_api_key,
            temperature=0.7,
        )
    
    # Try Groq
    if settings.groq_api_key and ChatOpenAI:
        return ChatOpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=settings.groq_api_key,
            model=os.getenv("GROQ_MODEL", "llama3-8b-8192"),
            temperature=0.7,
        )
    
    raise RuntimeError("No LLM provider configured (need GEMINI_API_KEY or GROQ_API_KEY)")


def run_chat_agent(question: str, db: Session) -> ChatResponse:
    """Run chat agent with automatic tool selection based on question keywords."""
    
    # Get LLM
    llm = _get_llm()
    
    # Get available tools
    tools = get_all_tools()
    tool_calls = []
    tool_results = {}
    
    # RAG retrieval
    rag_contexts = []
    if db is not None:
        retriever = build_retriever(db)
        rag_docs = retriever.search(question, k=3)
        rag_contexts = [
            RAGContext(content=doc.content, source=doc.source, score=doc.score)
            for doc in rag_docs
        ]
    
    # Smart tool selection based on question keywords
    question_lower = question.lower()
    
    # Weather tool
    if any(word in question_lower for word in ["weather", "temperature", "rain", "conditions", "forecast"]):
        from app.services.agent_tools import check_weather_conditions
        import re
        
        # Extract location from question using multiple strategies
        location = None
        
        # Strategy 1: Look for "in <location>" or "at <location>"
        location_match = re.search(r'\b(?:in|at|for)\s+([a-z\s,.-]+?)(?:\?|$|\s+(?:check|today|now|please))', question_lower)
        if location_match:
            location = location_match.group(1).strip()
        
        # Strategy 2: Check for known cities/countries
        if not location:
            known_places = [
                "egypt", "cairo", "alexandria",
                "san francisco", "los angeles", "new york", "chicago", "houston",
                "london", "paris", "tokyo", "dubai", "singapore",
                "boston", "seattle", "miami", "dallas", "denver"
            ]
            for place in known_places:
                if place in question_lower:
                    location = place
                    break
        
        # Default fallback
        if not location:
            location = "san francisco"
        
        try:
            result = check_weather_conditions.invoke({"location": location})
            tool_calls.append(ToolCall(tool="check_weather_conditions", arguments={"location": location}, output=result))
            tool_results["weather"] = result
        except Exception as e:
            tool_results["weather"] = f"Error: {e}"
    
    # Route calculations
    if any(word in question_lower for word in ["calculate", "metrics", "distance", "fuel", "cost", "time"]):
        from app.services.agent_tools import calculate_route_metrics
        # Extract approximate values from question
        import re
        distance_match = re.search(r'(\d+)\s*(km|kilometer)', question_lower)
        stops_match = re.search(r'(\d+)\s*stop', question_lower)
        
        route_data = {
            "distance_km": int(distance_match.group(1)) if distance_match else 100,
            "num_stops": int(stops_match.group(1)) if stops_match else 5,
            "area_type": "urban" if "city" in question_lower or "urban" in question_lower else "highway",
            "vehicle_type": "van" if "van" in question_lower else "truck" if "truck" in question_lower else "van"
        }
        
        try:
            result = calculate_route_metrics.run(route_data)
            tool_calls.append(ToolCall(tool="calculate_route_metrics", arguments=route_data, output=result))
            tool_results["metrics"] = result
        except Exception as e:
            tool_results["metrics"] = f"Error: {e}"
    
    # Traffic conditions
    if any(word in question_lower for word in ["traffic", "congestion", "delay", "rush hour"]):
        from app.services.agent_tools import check_traffic_conditions
        from datetime import datetime
        import re
        
        # Extract location using same strategy as weather
        location = None
        location_match = re.search(r'\b(?:in|at|for)\s+([a-z\s,.-]+?)(?:\?|$|\s+(?:check|today|now|please))', question_lower)
        if location_match:
            location = location_match.group(1).strip()
        
        if not location:
            known_places = ["egypt", "cairo", "san francisco", "los angeles", "new york", "chicago", "boston"]
            for place in known_places:
                if place in question_lower:
                    location = place
                    break
        
        if not location:
            location = "downtown"
        
        time_of_day = datetime.now().strftime("%H:%M")
        if "morning" in question_lower:
            time_of_day = "08:00"
        elif "afternoon" in question_lower or "evening" in question_lower:
            time_of_day = "17:00"
        
        try:
            result = check_traffic_conditions.invoke({"location": location, "time_of_day": time_of_day})
            tool_calls.append(ToolCall(tool="check_traffic_conditions", arguments={"location": location, "time_of_day": time_of_day}, output=result))
            tool_results["traffic"] = result
        except Exception as e:
            tool_results["traffic"] = f"Error: {e}"
    
    # Optimization
    if any(word in question_lower for word in ["optimize", "order", "sequence", "priority", "arrange"]):
        tool_results["optimization"] = "For route optimization, please provide a RouteRequest with stops, priorities, and time windows."
    
    # Validation
    if any(word in question_lower for word in ["validate", "check", "verify", "feasible"]):
        tool_results["validation"] = "For route validation, please provide a RouteRequest with planned start time, stops, and constraints."
    
    # Web search for current events, news, or topics not in knowledge base
    if any(word in question_lower for word in ["search", "find", "look up", "latest", "current", "news", "what is", "who is", "when did"]):
        from app.services.agent_tools import web_search
        try:
            # Extract search query - remove question words
            search_query = question_lower
            for prefix in ["search for", "find", "look up", "what is", "who is", "tell me about", "when did"]:
                if question_lower.startswith(prefix):
                    search_query = question_lower[len(prefix):].strip()
                    break
            
            result = web_search.invoke({"query": search_query, "num_results": 3})
            tool_calls.append(ToolCall(tool="web_search", arguments={"query": search_query}, output=result))
            tool_results["web_search"] = result
        except Exception as e:
            tool_results["web_search"] = f"Error: {e}"
    
    # Wikipedia for encyclopedia information
    if any(word in question_lower for word in ["wikipedia", "encyclopedia", "definition", "explain", "what are", "history of", "about"]):
        from app.services.agent_tools import wikipedia_search
        try:
            # Extract topic
            wiki_query = question_lower
            for prefix in ["tell me about", "what is", "what are", "explain", "define", "wikipedia"]:
                if question_lower.startswith(prefix):
                    wiki_query = question_lower[len(prefix):].strip()
                    break
            
            # Remove question marks and clean up
            wiki_query = wiki_query.replace("?", "").strip()
            
            result = wikipedia_search.invoke({"query": wiki_query})
            tool_calls.append(ToolCall(tool="wikipedia_search", arguments={"query": wiki_query}, output=result))
            tool_results["wikipedia"] = result
        except Exception as e:
            tool_results["wikipedia"] = f"Error: {e}"
    
    # Build context for LLM
    tool_context = ""
    if tool_results:
        tool_context = "\n\n".join([
            f"=== {key.upper()} ===\n{value}"
            for key, value in tool_results.items()
        ])
    
    if rag_contexts:
        rag_text = "\n".join([f"- ({ctx.source}) {ctx.content[:200]}..." for ctx in rag_contexts])
        tool_context += f"\n\n=== KNOWLEDGE BASE ===\n{rag_text}"
    
    # Create prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert logistics route planning assistant.

Answer the user's question based on the tool results and knowledge base below.
Be concise, practical, and actionable. If you used tools, incorporate their results.

Tool Results:
{tool_context}"""),
        ("human", "{question}")
    ])
    
    # Invoke LLM
    try:
        chain = prompt | llm
        response = chain.invoke({
            "tool_context": tool_context if tool_context else "No tools were needed for this question.",
            "question": question,
        })
        
        # Extract answer
        if hasattr(response, "content"):
            answer = response.content
        else:
            answer = str(response)
        
        return ChatResponse(
            answer=answer,
            tool_calls=tool_calls,
            rag_contexts=rag_contexts,
        )
    
    except Exception as e:
        # Fallback response
        return ChatResponse(
            answer=f"I encountered an error: {e}. However, I can tell you that I have access to weather data, route calculations, traffic analysis, and best practices documentation. How can I help you with route planning?",
            tool_calls=tool_calls,
            rag_contexts=rag_contexts,
        )
