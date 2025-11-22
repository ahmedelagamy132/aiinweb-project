"""FastAPI application entry point used by the lab backend container."""

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import Base, engine
from app.routers.agent import router as agent_router
from app.routers.chat import router as chat_router
from app.routers.echo import router as echo_router
from app.routers.gemini import router as gemini_router
from app.routers.planner import router as planner_router
from app.routers.resources import router as resources_router

# Load environment variables from a local .env file when present so the
# application picks up credentials configured for the labs.
load_dotenv()

settings = get_settings()
Base.metadata.create_all(bind=engine)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agent_router)
app.include_router(chat_router)
app.include_router(echo_router)
app.include_router(gemini_router)
app.include_router(planner_router)
app.include_router(resources_router)


@app.get("/health")
def health() -> dict[str, str]:
    """Report service status for lab curl checks and container health probes."""

    return {"status": "ok"}
