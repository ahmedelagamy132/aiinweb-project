"""Geocoding utilities for converting coordinates to locations and vice versa."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.agent_tools import reverse_geocode_mapbox

router = APIRouter(prefix="/geocoding", tags=["geocoding"])


class ReverseGeocodeRequest(BaseModel):
    """Request to convert coordinates to location name."""
    latitude: float = Field(..., ge=-90, le=90, description="Latitude coordinate")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude coordinate")


class ReverseGeocodeResponse(BaseModel):
    """Location information from coordinates."""
    place_name: str
    city: str | None = None
    region: str | None = None
    country: str | None = None
    formatted: str
    coordinates: dict[str, float]


@router.post("/reverse", response_model=ReverseGeocodeResponse)
def reverse_geocode(request: ReverseGeocodeRequest) -> ReverseGeocodeResponse:
    """
    Convert latitude/longitude coordinates to a readable location name.
    
    Uses MapBox Geocoding API to perform reverse geocoding.
    
    Example:
    ```json
    {
      "latitude": 37.7749,
      "longitude": -122.4194
    }
    ```
    
    Returns:
    ```json
    {
      "place_name": "San Francisco, California, United States",
      "city": "San Francisco",
      "region": "California",
      "country": "United States",
      "formatted": "San Francisco, CA",
      "coordinates": {"latitude": 37.7749, "longitude": -122.4194}
    }
    ```
    """
    result = reverse_geocode_mapbox(request.latitude, request.longitude)
    
    if not result:
        raise HTTPException(
            status_code=503,
            detail="Reverse geocoding failed. Ensure MAPBOX_API_KEY is configured."
        )
    
    return ReverseGeocodeResponse(**result)
