"""Router package with all API endpoints."""

from app.routers.agent import router as agent_router
from app.routers.echo import router as echo_router
from app.routers.gemini import router as gemini_router
from app.routers.planner import router as planner_router

__all__ = ["agent_router", "echo_router", "gemini_router", "planner_router"]
