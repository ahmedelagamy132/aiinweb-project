"""FastAPI application entry point for the Logistics Route Planner."""

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import Base, engine
from app.routers.agent import router as agent_router
from app.routers.echo import router as echo_router
from app.routers.gemini import router as gemini_router
from app.routers.planner import router as planner_router

# Load environment variables from a local .env file when present
load_dotenv()

settings = get_settings()
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Logistics Route Planner Launch Assistant",
    description="AI-powered logistics route planning with Gemini and RAG",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agent_router)
app.include_router(echo_router)
app.include_router(gemini_router)
app.include_router(planner_router)


@app.get("/health")
def health() -> dict[str, str]:
    """Report service status for health checks and container probes."""
    return {"status": "ok"}


@app.get("/echo")
def echo_get() -> dict[str, str]:
    """Simple echo endpoint for testing."""
    return {"message": "Echo service is running"}
