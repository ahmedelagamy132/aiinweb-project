"""Route validation agent service - redirects to LangChain implementation.

This module provides backward compatibility by importing from agent_langchain.
All route validation logic now uses real tools (weather API, calculations, etc.)
instead of mock data.
"""

from __future__ import annotations

# Import everything from the LangChain implementation
from app.services.agent_langchain import (
    AgentServiceError,
    AgentToolCall,
    RAGContext,
    run_route_validation_agent,
    get_agent_history,
)

__all__ = [
    "AgentServiceError",
    "AgentToolCall", 
    "RAGContext",
    "run_route_validation_agent",
    "get_agent_history",
]
