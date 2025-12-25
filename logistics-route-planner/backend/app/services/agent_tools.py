"""Real LangChain tools for route planning and logistics operations.

This module implements practical tools using real APIs and calculations:
- Weather data from Open-Meteo API
- Traffic and routing calculations using MapBox API (primary), Google Maps (fallback)
- Route validation and optimization with real geocoding
"""

from __future__ import annotations

import json
import os
from typing import Any
import re
from datetime import datetime, timedelta

from langchain_core.tools import tool
import requests
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

from app.config import get_settings

# Try to import googlemaps, make it optional
try:
    import googlemaps
    GOOGLE_MAPS_AVAILABLE = True
except ImportError:
    GOOGLE_MAPS_AVAILABLE = False


def _get_mapbox_client():
    """Lazily get MapBox client configuration."""
    settings = get_settings()
    if settings.mapbox_api_key:
        return {"api_key": settings.mapbox_api_key, "base_url": "https://api.mapbox.com"}
    return None


def _get_gmaps_client():
    """Lazily get Google Maps client."""
    if not GOOGLE_MAPS_AVAILABLE:
        return None
    settings = get_settings()
    if settings.google_maps_api_key:
        return googlemaps.Client(key=settings.google_maps_api_key)
    return None


def reverse_geocode_mapbox(latitude: float, longitude: float) -> dict[str, Any] | None:
    """
    Convert coordinates to a city/place name using MapBox Geocoding API.
    
    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate
    
    Returns:
        Dictionary with place information or None if failed:
        {
            "place_name": "San Francisco, California, United States",
            "city": "San Francisco",
            "region": "California",
            "country": "United States",
            "formatted": "San Francisco, CA"
        }
    """
    mapbox_client = _get_mapbox_client()
    if not mapbox_client:
        return None
    
    try:
        url = f"{mapbox_client['base_url']}/geocoding/v5/mapbox.places/{longitude},{latitude}.json"
        params = {
            "access_token": mapbox_client["api_key"],
            "types": "place,locality,region,country"
        }
        
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        if data.get("features"):
            feature = data["features"][0]
            place_name = feature.get("place_name", "")
            
            # Extract city, region, country from context
            city = None
            region = None
            country = None
            
            for ctx in feature.get("context", []):
                ctx_id = ctx.get("id", "")
                if ctx_id.startswith("place."):
                    city = ctx.get("text")
                elif ctx_id.startswith("region."):
                    region = ctx.get("text")
                elif ctx_id.startswith("country."):
                    country = ctx.get("text")
            
            # If no city in context, use the main text
            if not city:
                city = feature.get("text")
            
            # Build formatted short name
            formatted_parts = [city] if city else []
            if region:
                # Try to get short code for US states
                region_code = region
                for ctx in feature.get("context", []):
                    if ctx.get("id", "").startswith("region."):
                        region_code = ctx.get("short_code", "").replace("US-", "")
                        break
                formatted_parts.append(region_code)
            
            formatted = ", ".join(formatted_parts) if formatted_parts else place_name
            
            return {
                "place_name": place_name,
                "city": city,
                "region": region,
                "country": country,
                "formatted": formatted,
                "coordinates": {"latitude": latitude, "longitude": longitude}
            }
        
        return None
        
    except Exception as e:
        print(f"MapBox reverse geocoding error: {e}")
        return None


COORD_PATTERN = re.compile(r"(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)")


def _extract_coordinates_from_text(text: str | None) -> tuple[float, float] | None:
    """Parse latitude/longitude pairs embedded in free-form text."""
    if not text:
        return None
    match = COORD_PATTERN.search(text)
    if match:
        try:
            lat = float(match.group(1))
            lon = float(match.group(2))
            return lat, lon
        except ValueError:
            return None
    return None


# ============================================================================
# WEATHER TOOLS (Using Open-Meteo Free API)
# ============================================================================

@tool
def check_weather_conditions(location: str) -> str:
    """Get current weather conditions for a location.
    
    Args:
        location: City name or coordinates (e.g., 'San Francisco' or '37.77,-122.41')
    
    Returns:
        JSON string with current weather data
    """
    try:
        city_coords = {
            "san francisco": (37.77, -122.41),
            "los angeles": (34.05, -118.24),
            "new york": (40.71, -74.01),
            "chicago": (41.88, -87.63),
            "houston": (29.76, -95.37),
            "phoenix": (33.45, -112.07),
            "seattle": (47.61, -122.33),
            "denver": (39.74, -104.99),
            "miami": (25.76, -80.19),
            "boston": (42.36, -71.06),
        }
        
        coord_from_text = _extract_coordinates_from_text(location)
        if coord_from_text:
            lat, lon = coord_from_text
        elif ',' in location:
            try:
                lat_str, lon_str = location.split(',', 1)
                lat, lon = float(lat_str.strip()), float(lon_str.strip())
            except Exception:
                lat, lon = 37.77, -122.41
        else:
            location_lower = location.lower()
            lat, lon = city_coords.get(location_lower, (37.77, -122.41))
        
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,precipitation,weather_code,wind_speed_10m",
            "temperature_unit": "celsius",
            "wind_speed_unit": "mph",
            "precipitation_unit": "mm"
        }
        
        response = None
        last_exception: Exception | None = None
        for timeout in (5, 10):
            try:
                response = requests.get(url, params=params, timeout=timeout)
                response.raise_for_status()
                break
            except requests.exceptions.Timeout as exc:
                last_exception = exc
                response = None
            except requests.exceptions.RequestException as exc:
                last_exception = exc
                response = None
                break

        if response is None:
            raise last_exception or Exception("Weather request failed")

        data = response.json()
        
        current = data.get("current", {})
        weather_code = current.get("weather_code", 0)
        conditions = _interpret_weather_code(weather_code)

        temp_c = current.get("temperature_2m")
        temp_f = (temp_c * 9 / 5 + 32) if temp_c is not None else None
        humidity = current.get("relative_humidity_2m")
        precipitation_mm = current.get("precipitation", 0)
        wind_speed_mph = current.get("wind_speed_10m")
        wind_speed_kph = (wind_speed_mph * 1.60934) if wind_speed_mph is not None else None
        delivery_impact = _assess_delivery_impact(weather_code, wind_speed_mph or 0)

        if delivery_impact.startswith("HIGH"):
            alert_level = "alert"
        elif delivery_impact.startswith("MODERATE"):
            alert_level = "caution"
        else:
            alert_level = "normal"

        result = {
            "location": location,
            "coordinates": f"{lat},{lon}",
            "temperature_celsius": round(temp_c, 1) if temp_c is not None else None,
            "temperature_f": round(temp_f, 1) if temp_f is not None else None,
            "humidity_percent": round(humidity, 0) if humidity is not None else None,
            "precipitation_mm": round(precipitation_mm, 2),
            "wind_speed_mph": round(wind_speed_mph, 1) if wind_speed_mph is not None else None,
            "wind_speed_kph": round(wind_speed_kph, 1) if wind_speed_kph is not None else None,
            "current_conditions": conditions,
            "conditions": conditions,
            "alert_level": alert_level,
            "delivery_impact": delivery_impact,
            "data_source": "open-meteo"
        }
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        return json.dumps({
            "error": f"Failed to fetch weather: {str(e)}",
            "fallback": "Weather data unavailable. Assume normal conditions."
        }, indent=2)


def _interpret_weather_code(code: int) -> str:
    """Interpret WMO weather codes."""
    if code == 0:
        return "Clear sky"
    elif code in [1, 2, 3]:
        return "Partly cloudy"
    elif code in [45, 48]:
        return "Foggy"
    elif code in [51, 53, 55]:
        return "Drizzle"
    elif code in [61, 63, 65]:
        return "Rain"
    elif code in [71, 73, 75]:
        return "Snow"
    elif code in [95, 96, 99]:
        return "Thunderstorm"
    else:
        return "Variable conditions"


def _assess_delivery_impact(weather_code: int, wind_speed: float) -> str:
    """Assess how weather impacts delivery operations."""
    if weather_code >= 95:
        return "HIGH IMPACT: Severe weather may require route delays"
    elif weather_code in [71, 73, 75]:
        return "HIGH IMPACT: Snow requires slower speeds and delays"
    elif weather_code in [61, 63, 65]:
        return "MODERATE IMPACT: Rain may slow deliveries by 15-20%"
    elif wind_speed > 25:
        return "MODERATE IMPACT: High winds affect large vehicles"
    else:
        return "LOW IMPACT: Weather is favorable for deliveries"


# ============================================================================
# ROUTE CALCULATION TOOLS
# ============================================================================

@tool
def calculate_route_metrics(route_data: dict[str, Any]) -> str:
    """Calculate route metrics using MapBox Directions API with real traffic data.
    Falls back to Google Maps, then geocoding if unavailable.
    
    Args:
        route_data: Dictionary with start_location, stops (list with location field), vehicle_type
    
    Returns:
        JSON string with distance, time (with traffic), fuel, and cost estimates
    """
    try:
        start_location = route_data.get("start_location", "")
        stops = route_data.get("stops", [])
        vehicle_type = route_data.get("vehicle_type", "van")
        
        if not stops:
            return json.dumps({"error": "No stops provided"}, indent=2)

        entries: list[dict[str, Any]] = [
            {
                "raw": start_location,
                "lat": route_data.get("start_latitude"),
                "lon": route_data.get("start_longitude"),
            }
        ]
        for stop in stops:
            entries.append(
                {
                    "raw": stop.get("location", ""),
                    "lat": stop.get("latitude"),
                    "lon": stop.get("longitude"),
                }
            )

        def resolve_entry(entry: dict[str, Any]) -> tuple[float, float] | None:
            lat = entry.get("lat")
            lon = entry.get("lon")
            if lat is not None and lon is not None:
                return float(lat), float(lon)
            parsed = _extract_coordinates_from_text(entry.get("raw"))
            if parsed:
                return parsed
            return None

        # Try MapBox Directions API first (with real traffic)
        mapbox_client = _get_mapbox_client()
        if mapbox_client:
            geolocator = Nominatim(user_agent="logistics-route-planner")
            try:
                coordinates: list[str] = []
                for entry in entries:
                    resolved = resolve_entry(entry)
                    if resolved:
                        lat, lon = resolved
                        coordinates.append(f"{lon},{lat}")
                        continue

                    location = geolocator.geocode(entry.get("raw"))
                    if location:
                        coordinates.append(f"{location.longitude},{location.latitude}")
                    else:
                        raise Exception(f"Could not geocode: {entry.get('raw')}")

                coords_string = ";".join(coordinates)
                url = f"{mapbox_client['base_url']}/directions/v5/mapbox/driving-traffic/{coords_string}"
                params = {
                    "access_token": mapbox_client["api_key"],
                    "geometries": "geojson",
                    "overview": "full",
                    "steps": "false"
                }

                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()

                if data.get("routes"):
                    route = data["routes"][0]
                    total_distance_km = route["distance"] / 1000  # meters to km
                    total_time_hours = route["duration"] / 3600  # seconds to hours

                    service_time_hours = (len(stops) * 5) / 60
                    total_time_hours += service_time_hours

                    fuel_rates = {"van": 9.0, "truck": 15.0, "motorcycle": 5.0}
                    fuel_rate = fuel_rates.get(vehicle_type, 10.0)
                    fuel_liters = (total_distance_km / 100) * fuel_rate
                    fuel_cost_usd = (fuel_liters / 3.785) * 3.50
                    co2_kg = fuel_liters * 2.68

                    result = {
                        "distance_km": round(total_distance_km, 2),
                        "distance_miles": round(total_distance_km * 0.621371, 2),
                        "estimated_time_hours": round(total_time_hours, 2),
                        "estimated_time_formatted": f"{int(total_time_hours)}h {int((total_time_hours % 1) * 60)}min",
                        "fuel_consumption_liters": round(fuel_liters, 2),
                        "estimated_fuel_cost_usd": round(fuel_cost_usd, 2),
                        "co2_emissions_kg": round(co2_kg, 2),
                        "data_source": "mapbox_real_traffic",
                        "includes_current_traffic": True
                    }

                    return json.dumps(result, indent=2)

            except Exception as e:
                print(f"MapBox API error: {e}, trying Google Maps fallback")

        # Try Google Maps Distance Matrix API (fallback)
        gmaps = _get_gmaps_client()
        if gmaps:
            try:
                def format_for_google(entry: dict[str, Any]) -> str:
                    resolved = resolve_entry(entry)
                    if resolved:
                        lat, lon = resolved
                        return f"{lat},{lon}"
                    return entry.get("raw", "")

                locations = [format_for_google(entry) for entry in entries]
                total_distance_km = 0.0
                total_time_hours = 0.0

                for i in range(len(locations) - 1):
                    result = gmaps.distance_matrix(
                        origins=[locations[i]],
                        destinations=[locations[i + 1]],
                        mode="driving",
                        departure_time="now",
                        traffic_model="best_guess"
                    )

                    if result['rows'][0]['elements'][0]['status'] == 'OK':
                        distance_m = result['rows'][0]['elements'][0]['distance']['value']
                        duration_s = result['rows'][0]['elements'][0]['duration_in_traffic']['value']
                        total_distance_km += distance_m / 1000
                        total_time_hours += duration_s / 3600

                service_time_hours = (len(stops) * 5) / 60
                total_time_hours += service_time_hours

                fuel_rates = {"van": 9.0, "truck": 15.0, "motorcycle": 5.0}
                fuel_rate = fuel_rates.get(vehicle_type, 10.0)
                fuel_liters = (total_distance_km / 100) * fuel_rate
                fuel_cost_usd = (fuel_liters / 3.785) * 3.50
                co2_kg = fuel_liters * 2.68

                result = {
                    "distance_km": round(total_distance_km, 2),
                    "distance_miles": round(total_distance_km * 0.621371, 2),
                    "estimated_time_hours": round(total_time_hours, 2),
                    "estimated_time_formatted": f"{int(total_time_hours)}h {int((total_time_hours % 1) * 60)}min",
                    "fuel_consumption_liters": round(fuel_liters, 2),
                    "estimated_fuel_cost_usd": round(fuel_cost_usd, 2),
                    "co2_emissions_kg": round(co2_kg, 2),
                    "data_source": "google_maps_real_traffic (fallback)",
                    "includes_current_traffic": True
                }

                return json.dumps(result, indent=2)

            except Exception as e:
                print(f"Google Maps API error: {e}, falling back to geocoding")

        # Fallback: Use geopy for distance estimation
        geolocator = Nominatim(user_agent="logistics-route-planner")
        coordinates = []

        for entry in entries:
            resolved = resolve_entry(entry)
            if resolved:
                coordinates.append(resolved)
                continue
            location = geolocator.geocode(entry.get("raw"))
            coordinates.append((location.latitude, location.longitude) if location else None)

        total_distance_km = 0.0
        for i in range(len(coordinates) - 1):
            if coordinates[i] and coordinates[i + 1]:
                total_distance_km += geodesic(coordinates[i], coordinates[i + 1]).kilometers
        
        # Estimate time (average 45 km/h in mixed traffic)
        driving_time_hours = total_distance_km / 45
        service_time_hours = (len(stops) * 5) / 60
        total_time_hours = driving_time_hours + service_time_hours
        
        # Calculate costs
        fuel_rates = {"van": 9.0, "truck": 15.0, "motorcycle": 5.0}
        fuel_rate = fuel_rates.get(vehicle_type, 10.0)
        fuel_liters = (total_distance_km / 100) * fuel_rate
        fuel_cost_usd = (fuel_liters / 3.785) * 3.50
        co2_kg = fuel_liters * 2.68
        
        result = {
            "distance_km": round(total_distance_km, 2),
            "distance_miles": round(total_distance_km * 0.621371, 2),
            "estimated_time_hours": round(total_time_hours, 2),
            "estimated_time_formatted": f"{int(total_time_hours)}h {int((total_time_hours % 1) * 60)}min",
            "fuel_consumption_liters": round(fuel_liters, 2),
            "estimated_fuel_cost_usd": round(fuel_cost_usd, 2),
            "co2_emissions_kg": round(co2_kg, 2),
            "data_source": "geopy_estimated",
            "includes_current_traffic": False
        }
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        return json.dumps({"error": f"Calculation failed: {str(e)}"}, indent=2)


def _calculate_efficiency_rating(distance_km: float, stops: int, time_hours: float) -> str:
    """Calculate efficiency rating."""
    if stops == 0 or time_hours == 0:
        return "INSUFFICIENT DATA"
    
    stops_per_hour = stops / time_hours
    km_per_stop = distance_km / stops
    
    if 5 <= stops_per_hour <= 8 and 5 <= km_per_stop <= 15:
        return "EXCELLENT"
    elif 3 <= stops_per_hour <= 10 and 3 <= km_per_stop <= 20:
        return "GOOD"
    else:
        return "NEEDS OPTIMIZATION"


# ============================================================================
# ROUTE VALIDATION TOOLS
# ============================================================================

@tool
def validate_route_timing(route_request: dict[str, Any]) -> str:
    """Validate if delivery stops can be completed within time windows.
    
    Args:
        route_request: Dictionary matching RouteRequest schema
    
    Returns:
        JSON string with validation results
    """
    try:
        stops = route_request.get("stops", [])
        constraints = route_request.get("constraints", {})
        start_time_str = route_request.get("planned_start_time", "")
        
        try:
            start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
        except:
            start_time = datetime.now()
        
        issues = []
        warnings = []
        current_time = start_time
        
        for idx, stop in enumerate(stops):
            stop_id = stop.get("stop_id", f"stop_{idx}")
            
            if idx > 0:
                current_time += timedelta(minutes=15)
            current_time += timedelta(minutes=5)
            
            window_start = stop.get("time_window_start")
            window_end = stop.get("time_window_end")
            
            if window_start and window_end:
                stop_time_str = current_time.strftime("%H:%M")
                if stop_time_str < window_start:
                    warnings.append(f"{stop_id}: Early arrival at {stop_time_str}")
                elif stop_time_str > window_end:
                    issues.append(f"{stop_id}: Late arrival at {stop_time_str}")
        
        driver_shift_end = constraints.get("driver_shift_end")
        if driver_shift_end and current_time.strftime("%H:%M") > driver_shift_end:
            issues.append(f"Route exceeds driver shift end at {driver_shift_end}")
        
        actual_duration = (current_time - start_time).total_seconds() / 3600
        max_duration = constraints.get("max_route_duration_hours")
        if max_duration and actual_duration > max_duration:
            issues.append(f"Duration {actual_duration:.1f}h exceeds maximum {max_duration}h")
        
        result = {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "total_duration_hours": round(actual_duration, 2)
        }
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        return json.dumps({"error": f"Validation failed: {str(e)}"}, indent=2)


@tool
def optimize_stop_sequence(route_request: dict[str, Any]) -> str:
    """Provide comprehensive stop data for LLM-based route optimization.
    
    This tool does NOT apply rule-based optimization. Instead, it provides all relevant
    data about stops so the LLM can intelligently decide the best sequence based on:
    - Priorities (high/normal/low)
    - Time windows (start/end times)
    - Geographic locations (lat/lng)
    - Current sequence order
    
    The LLM will analyze this data and recommend the optimal sequence.
    
    Args:
        route_request: Dictionary matching RouteRequest schema
    
    Returns:
        JSON string with comprehensive stop data for LLM analysis
    """
    try:
        stops = route_request.get("stops", [])
        
        if len(stops) <= 2:
            return json.dumps({
                "status": "no_optimization_needed",
                "reason": "Only 2 or fewer stops - no optimization possible",
                "stop_count": len(stops)
            }, indent=2)
        
        # Prepare comprehensive stop data for LLM analysis
        stop_details = []
        for stop in sorted(stops, key=lambda x: x.get("sequence_number", 0)):
            stop_details.append({
                "stop_id": stop.get("stop_id"),
                "current_position": stop.get("sequence_number"),
                "label": stop.get("label", f"Stop {stop.get('sequence_number')}"),
                "location": stop.get("location"),
                "coordinates": {
                        "lat": stop.get("latitude"),
                        "lng": stop.get("longitude")
                },
                "priority": stop.get("priority", "normal"),
                "time_window": {
                    "start": stop.get("time_window_start", "not specified"),
                    "end": stop.get("time_window_end", "not specified")
                }
            })
        
        result = {
            "status": "ready_for_optimization",
            "total_stops": len(stops),
            "stops": stop_details,
            "current_sequence": [s["stop_id"] for s in stop_details],
            "optimization_factors": [
                "Priority levels (high priority customers should be served first)",
                "Time windows (avoid late arrivals and minimize waiting time)",
                "Geographic proximity (reduce backtracking and travel distance)",
                "Service efficiency (balance all factors for best overall route)"
            ],
            "instruction_for_llm": "Analyze the stops above and recommend the optimal delivery sequence. Consider priorities, time windows, and geographic locations. Explain your reasoning."
        }
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        return json.dumps({"error": f"Failed to prepare optimization data: {str(e)}"}, indent=2)


@tool  
def check_traffic_conditions(location: str, time_of_day: str = "now") -> str:
    """Get real-time traffic conditions using MapBox Traffic API.
    Falls back to a time-of-day estimate when MapBox data is unavailable.
    
    Args:
        location: City or area name (e.g., "Downtown Los Angeles")
        time_of_day: When to check - 'now', HH:MM format, or 'morning'/'afternoon'/'evening'
    
    Returns:
        JSON string with traffic level, delay factor, and recommendations
    """
    try:
        # Try MapBox Directions API with traffic first
        mapbox_client = _get_mapbox_client()
        if mapbox_client:
            try:
                # First try to extract coordinates from the location string
                coord_from_text = _extract_coordinates_from_text(location)
                if coord_from_text:
                    lat, lon = coord_from_text
                else:
                    # Fall back to geocoding
                    geolocator = Nominatim(user_agent="logistics-route-planner")
                    location_obj = geolocator.geocode(location)
                    
                    if not location_obj:
                        raise Exception(f"Could not geocode location: {location}")
                    
                    lon, lat = location_obj.longitude, location_obj.latitude
                
                if lat and lon:
                    
                    # Create a short route to sample traffic (5km offset)
                    offset = 0.05  # approximately 5km
                    start_coords = f"{lon},{lat}"
                    end_coords = f"{lon + offset},{lat}"
                    
                    # Get route with traffic
                    url = f"{mapbox_client['base_url']}/directions/v5/mapbox/driving-traffic/{start_coords};{end_coords}"
                    params = {
                        "access_token": mapbox_client["api_key"],
                        "overview": "false"
                    }
                    
                    response = requests.get(url, params=params, timeout=10)
                    response.raise_for_status()
                    data = response.json()
                    
                    if data.get("routes"):
                        route = data["routes"][0]
                        duration_with_traffic = route["duration"]  # seconds
                        
                        # Get route without traffic (free-flow)
                        url_no_traffic = f"{mapbox_client['base_url']}/directions/v5/mapbox/driving/{start_coords};{end_coords}"
                        response_no_traffic = requests.get(url_no_traffic, params=params, timeout=10)
                        data_no_traffic = response_no_traffic.json()
                        
                        if data_no_traffic.get("routes"):
                            duration_normal = data_no_traffic["routes"][0]["duration"]
                            
                            # Calculate delay factor
                            if duration_normal > 0:
                                delay_factor = duration_with_traffic / duration_normal
                            else:
                                delay_factor = 1.0
                            
                            # Categorize traffic level
                            if delay_factor >= 1.4:
                                traffic_level = "heavy"
                            elif delay_factor >= 1.15:
                                traffic_level = "moderate"
                            else:
                                traffic_level = "light"
                            
                            result_data = {
                                "location": location,
                                "traffic_level": traffic_level,
                                "delay_factor": round(delay_factor, 2),
                                "delay_minutes": round((duration_with_traffic - duration_normal) / 60, 1),
                                "recommendation": _traffic_recommendation(traffic_level),
                                "data_source": "mapbox_real_traffic",
                                "timestamp": datetime.now().isoformat()
                            }
                            
                            return json.dumps(result_data, indent=2)
                    
            except Exception as e:
                print(f"MapBox traffic API error: {e}, using fallback estimate")
        
        # Fallback: Time-based traffic estimation
        current_hour = datetime.now().hour
        
        # Parse time_of_day if it's in HH:MM format
        if ":" in time_of_day:
            try:
                check_hour = int(time_of_day.split(":")[0])
            except:
                check_hour = current_hour
        elif time_of_day == "morning":
            check_hour = 8
        elif time_of_day == "afternoon":
            check_hour = 14
        elif time_of_day == "evening":
            check_hour = 17
        else:
            check_hour = current_hour
        
        # Determine traffic level based on time
        if 7 <= check_hour <= 9 or 16 <= check_hour <= 18:
            traffic_level = "heavy"
            delay_factor = 1.5
        elif 10 <= check_hour <= 15:
            traffic_level = "moderate"
            delay_factor = 1.2
        else:
            traffic_level = "light"
            delay_factor = 1.0
        
        result_data = {
            "location": location,
            "time_checked": f"{check_hour:02d}:00",
            "traffic_level": traffic_level,
            "delay_factor": delay_factor,
            "recommendation": _traffic_recommendation(traffic_level),
            "data_source": "time_based_estimate",
            "note": "Configure MAPBOX_API_KEY for live traffic data"
        }
        
        return json.dumps(result_data, indent=2)
        
    except Exception as e:
        return json.dumps({"error": f"Traffic check failed: {str(e)}"}, indent=2)


def _traffic_recommendation(level: str) -> str:
    """Get traffic recommendation."""
    if level == "heavy":
        return "Allow extra 50% time buffer"
    elif level == "moderate":
        return "Allow 20% time buffer"
    else:
        return "Good conditions for on-time deliveries"


@tool
def web_search(query: str, num_results: int = 3) -> str:
    """Search the web using DuckDuckGo for real-time information.
    
    Args:
        query: Search query string
        num_results: Number of results to return (default: 3)
    
    Returns:
        JSON string with search results including titles, snippets, and URLs
    """
    try:
        from duckduckgo_search import DDGS
        
        results = []
        with DDGS() as ddgs:
            search_results = list(ddgs.text(query, max_results=num_results))
            
            for idx, result in enumerate(search_results, 1):
                results.append({
                    "position": idx,
                    "title": result.get("title", ""),
                    "snippet": result.get("body", ""),
                    "url": result.get("href", ""),
                })
        
        return json.dumps({
            "query": query,
            "num_results": len(results),
            "results": results
        }, indent=2)
        
    except ImportError:
        return json.dumps({
            "error": "DuckDuckGo search library not installed. Install with: pip install duckduckgo-search"
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Web search failed: {str(e)}"}, indent=2)


@tool
def wikipedia_search(query: str) -> str:
    """Search Wikipedia for encyclopedia information on a topic.
    
    Args:
        query: Topic to search for on Wikipedia
    
    Returns:
        JSON string with Wikipedia article summary and URL
    """
    try:
        import wikipediaapi
        
        wiki = wikipediaapi.Wikipedia(
            user_agent='LogisticsRoutePlanner/1.0 (contact@example.com)',
            language='en'
        )
        
        # Get the page
        page = wiki.page(query)
        
        if not page.exists():
            # Try to search for similar pages
            return json.dumps({
                "query": query,
                "found": False,
                "message": f"No Wikipedia article found for '{query}'. Try being more specific or check spelling."
            }, indent=2)
        
        # Get summary (first 5 sentences approximately)
        summary_text = page.summary
        sentences = summary_text.split('. ')[:5]
        summary = '. '.join(sentences) + ('.' if not sentences[-1].endswith('.') else '')
        
        return json.dumps({
            "query": query,
            "found": True,
            "title": page.title,
            "summary": summary,
            "url": page.fullurl,
            "categories": list(page.categories.keys())[:5] if page.categories else []
        }, indent=2)
            
    except ImportError:
        return json.dumps({
            "error": "Wikipedia library not installed. Install with: pip install wikipedia-api"
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Wikipedia search failed: {str(e)}"}, indent=2)


def get_all_tools():
    """Get all available tools for the route planning agent."""
    return [
        check_weather_conditions,
        calculate_route_metrics,
        validate_route_timing,
        optimize_stop_sequence,
        check_traffic_conditions,
        web_search,
        wikipedia_search,
    ]
