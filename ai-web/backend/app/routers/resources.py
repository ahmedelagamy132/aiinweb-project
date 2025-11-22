"""HTTP routes for the resource catalog."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import ResourceCreate, ResourceOut
from app.services.resources import create_resource, list_resources

router = APIRouter(prefix="/resources", tags=["resources"])


@router.get("/", response_model=list[ResourceOut])
def get_resources(db: Session = Depends(get_db)) -> list[ResourceOut]:
    """Return all resources stored in the database."""

    return [ResourceOut.model_validate(resource) for resource in list_resources(db)]


@router.post("/", response_model=ResourceOut)
def post_resource(payload: ResourceCreate, db: Session = Depends(get_db)) -> ResourceOut:
    """Create a new resource entry and return it to the client."""

    # Use JSON mode to coerce pydantic types (e.g., HttpUrl) into plain strings for
    # the SQLAlchemy model, preventing PostgreSQL adaptation errors.
    record = create_resource(db, **payload.model_dump(mode="json"))
    return ResourceOut.model_validate(record)

