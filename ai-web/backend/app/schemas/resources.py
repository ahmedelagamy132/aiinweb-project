"""Pydantic schemas for the resource catalog feature."""

from __future__ import annotations

from pydantic import BaseModel, Field, HttpUrl


class ResourceCreate(BaseModel):
    """Payload submitted from the React form."""

    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=10, max_length=1000)
    url: HttpUrl
    difficulty: str = Field(default="intermediate")


class ResourceOut(ResourceCreate):
    """Response model returned to clients."""

    id: int

    class Config:
        from_attributes = True

