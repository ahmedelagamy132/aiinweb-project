# Route Validation Agent - Technical Documentation

## Agent Architecture

The route validation agent is implemented in `app/services/agent_langchain.py` using the LangChain framework. The agent orchestrates multiple tools to validate delivery routes and provide actionable recommendations.

### Agent Workflow

1. **Tool Execution Phase**: The agent sequentially invokes tools to gather route data:
   - Weather conditions at start location
   - Route metrics (distance, time, fuel, cost)
   - Route timing validation
   - Stop sequence optimization
   - Traffic conditions
   - RAG retrieval for best practices

2. **Context Assembly**: Tool outputs are concatenated into a structured context string with clear section delimiters.

3. **LLM Analysis**: The agent sends the tool context and route details to an LLM (Gemini or Groq) with a system prompt that enforces a strict output format:
   ```
   VALID: true/false
   ISSUE: <specific problem>
   RECOMMENDATION: <actionable suggestion>
   OPTIMIZED_ORDER: stop_id1,stop_id2,stop_id3
   SUMMARY: <brief explanation>
   ```

4. **Result Parsing**: The agent parses the LLM response line-by-line to extract validation status, issues, recommendations, and optimized stop order.

5. **Deterministic Plan Building**: Using `_build_structured_action_plan()`, the agent constructs a step-by-step execution plan by synthesizing tool outputs:
   - Step 1: Plot delivery path with MapBox waypoints
   - Step 2: Review MapBox metrics (distance, time, fuel, cost, CO₂)
   - Step 3: Brief driver on weather conditions
   - Step 4: Incorporate traffic insights
   - Step 5: Confirm schedule alignment with constraints
   - Step 6: Dispatch instruction

6. **Persistence**: The agent saves results to the database via the `AgentRun` model, including tool calls, RAG contexts, and recommended actions.

### Tool Selection Logic

Tools are invoked unconditionally in a fixed sequence. The agent does not dynamically select tools based on route characteristics—all tools run for every validation request.

---

## Tools

### 1. check_weather_conditions

**Purpose**: Retrieve current weather data for a location to assess delivery impact.

**API**: Open-Meteo API (free, no key required)

**Inputs**:
- `location` (str): City name or "lat,lon" coordinates

**Process**:
1. Extract coordinates from location string using regex pattern `(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)`
2. If no coordinates found, look up common city defaults or use (37.77, -122.41)
3. Call Open-Meteo API with:
   - Temperature (°C and °F)
   - Humidity (%)
   - Precipitation (mm)
   - Wind speed (mph and km/h)
   - Weather code (0-99)
4. Interpret weather code to determine conditions (e.g., "Clear", "Rain", "Snow")
5. Assess delivery impact:
   - HIGH RISK: Severe weather (codes 95-99) or wind >40 mph
   - MODERATE CAUTION: Rain/snow or wind 25-40 mph
   - LOW IMPACT: Clear/cloudy conditions, wind <25 mph

**Output**: JSON with temperature, humidity, precipitation, wind, conditions, alert level, and delivery impact message.

---

### 2. calculate_route_metrics

**Purpose**: Calculate distance, duration (with traffic), fuel consumption, and cost using real routing APIs.

**API Priority**:
1. MapBox Directions API (primary) - `driving-traffic` profile
2. Google Maps Distance Matrix API (fallback)
3. Geopy geodesic calculation (final fallback)

**Inputs**:
- `route_data` (dict):
  - `start_location` (str)
  - `start_latitude`, `start_longitude` (float, optional)
  - `stops` (list): Each stop has `location`, `latitude`, `longitude`
  - `vehicle_type` (str): "van", "truck", "motorcycle"

**Process**:
1. Build coordinate list from start + stops
2. For each entry, resolve coordinates:
   - Use provided lat/lon if available
   - Extract from text via regex
   - Geocode location name using Nominatim
3. **MapBox Path**:
   - Join coordinates as `lon,lat;lon,lat;...`
   - Call `/directions/v5/mapbox/driving-traffic/{coordinates}`
   - Extract `distance` (meters) and `duration` (seconds) from first route
   - Add service time: 5 minutes per stop
4. **Google Maps Path**:
   - Call Distance Matrix API for each consecutive pair
   - Set `departure_time="now"` and `traffic_model="best_guess"`
   - Sum distances and durations (including traffic)
5. **Geopy Path**:
   - Calculate geodesic distance between coordinate pairs
   - Estimate time at 45 km/h average speed
6. Calculate costs:
   - Fuel rate: 9 L/100km (van), 15 L/100km (truck), 5 L/100km (motorcycle)
   - Fuel cost: (liters / 3.785) × $3.50
   - CO₂ emissions: liters × 2.68 kg/L

**Output**: JSON with distance, time, fuel consumption, cost, CO₂, data source, and traffic inclusion flag.

---

### 3. validate_route_timing

**Purpose**: Check if route can be completed within time windows and constraints.

**Inputs**:
- `route_request` (dict): Full route request with stops and constraints

**Process**:
1. Parse `planned_start_time` to datetime
2. Extract constraints:
   - `max_route_duration_hours`
   - `driver_shift_end`
   - `vehicle_capacity`
3. Iterate through stops in sequence:
   - Check if arrival falls within `time_window_start` and `time_window_end`
   - Flag violations
4. Calculate total route duration (driving + service time)
5. Compare against:
   - Max route duration
   - Driver shift end time
   - Vehicle capacity (sum of stop demands)

**Output**: JSON with:
- `is_valid` (bool)
- `issues` (list): Time window violations, capacity overages, shift overruns
- `total_duration_hours` (float)
- `constraint_violations` (list)

---

### 4. optimize_stop_sequence

**Purpose**: Provide comprehensive stop data for LLM-based route optimization.

**Note**: This tool does NOT apply rule-based optimization. It returns raw data for the LLM to analyze.

**Inputs**:
- `route_request` (dict): Route with stops

**Process**:
1. If ≤2 stops, return "no_optimization_needed"
2. Sort stops by current `sequence_number`
3. For each stop, extract:
   - `stop_id`, `label`, `location`
   - `coordinates` (lat/lon)
   - `priority` (high/normal/low)
   - `time_window` (start/end)
4. Build instruction for LLM: "Analyze stops and recommend optimal sequence considering priorities, time windows, and geographic proximity."

**Output**: JSON with:
- `status`: "ready_for_optimization"
- `total_stops` (int)
- `stops` (list): Detailed stop info
- `current_sequence` (list): Current stop IDs
- `optimization_factors` (list): Criteria for LLM

---

### 5. check_traffic_conditions

**Purpose**: Get real-time traffic delay factors for a location.

**API Priority**:
1. MapBox Directions API (primary) - `driving-traffic` vs. `driving` comparison
2. Time-based estimation (fallback)

**Inputs**:
- `location` (str): City name or coordinates
- `time_of_day` (str): "now", "HH:MM", "morning", "afternoon", "evening"

**Process**:
1. Resolve location to coordinates (same as weather tool)
2. **MapBox Path**:
   - Create short route (~5km): from `lon,lat` to `lon+0.05,lat`
   - Call `/directions/v5/mapbox/driving-traffic/{coords}` → duration with traffic
   - Call `/directions/v5/mapbox/driving/{coords}` → duration without traffic
   - Calculate delay factor: `duration_traffic / duration_normal`
   - Categorize:
     - `delay_factor >= 1.4`: heavy
     - `delay_factor >= 1.15`: moderate
     - `delay_factor < 1.15`: light
   - Calculate delay minutes: `(duration_traffic - duration_normal) / 60`
3. **Time-Based Path**:
   - Parse time_of_day to hour
   - Apply rules:
     - 7-9 AM or 4-6 PM: heavy (1.5x)
     - 10 AM-3 PM: moderate (1.2x)
     - Other: light (1.0x)

**Output**: JSON with:
- `traffic_level` (str): "light", "moderate", "heavy"
- `delay_factor` (float): Multiplier for expected duration
- `delay_minutes` (float): Additional minutes due to traffic
- `recommendation` (str): Action suggestion
- `data_source` (str): "mapbox_real_traffic" or "time_based_estimate"

---

### 6. rag_retrieval

**Purpose**: Retrieve relevant knowledge base documents to inform route validation.

**Implemented in**: `app/services/rag.py`

**Inputs**:
- `query` (str): Search query
- `k` (int): Number of documents to retrieve (default: 3)

**Process**:
1. Load documents from `data/` directory:
   - `logistics_knowledge.txt`
   - `fleet_management.txt`
   - `dispatch_operations.txt`
2. Split documents into chunks (500 chars, 50 char overlap)
3. Create embeddings using HuggingFace model: `sentence-transformers/all-MiniLM-L6-v2`
4. Store embeddings in Chroma vector database (in-memory)
5. Perform similarity search for query
6. Return top-k most relevant chunks with source filenames

**Output**: List of `RAGContext` objects with:
- `content` (str): Document text
- `source` (str): Filename
- `score` (float): Similarity score (0-1)

---

## Configuration

### Environment Variables

All environment variables are loaded via `app/config.py` → `Settings` class:

- `GEMINI_API_KEY`: Google Gemini API key (LLM provider)
- `GROQ_API_KEY`: Groq API key (alternative LLM provider)
- `GROQ_MODEL`: Model name for Groq (e.g., `openai/gpt-oss-120b`)
- `MAPBOX_API_KEY`: MapBox API key for routing and traffic
- `GOOGLE_MAPS_API_KEY`: Google Maps API key (fallback)
- `DATABASE_URL`: PostgreSQL connection string
- `CORS_ORIGINS`: Comma-separated list of allowed origins

### LLM Selection

The agent uses `_get_llm()` to select the LLM provider:

1. If `GROQ_API_KEY` is set: Use Groq via OpenAI compatibility layer
2. Else if `GEMINI_API_KEY` is set: Use Google Gemini
3. Else: Raise error

---

## Data Flow

```
FastAPI Endpoint (/ai/validate-route)
    ↓
run_route_validation_agent(route_request)
    ↓
[Tool Execution]
    ├── check_weather_conditions → Open-Meteo API
    ├── calculate_route_metrics → MapBox/Google Maps API
    ├── validate_route_timing → Internal logic
    ├── optimize_stop_sequence → Data preparation
    ├── check_traffic_conditions → MapBox API
    └── rag_retrieval → Chroma vector DB
    ↓
[Context Assembly]
    Tool outputs → Formatted string with section headers
    ↓
[LLM Invocation]
    ChatPromptTemplate + Tool Context → Gemini/Groq
    ↓
[Response Parsing]
    Extract VALID/ISSUE/RECOMMENDATION/OPTIMIZED_ORDER/SUMMARY
    ↓
[Deterministic Plan Building]
    _build_structured_action_plan() → 6-step execution plan
    ↓
[Database Persistence]
    AgentRun model → PostgreSQL
    ↓
RouteValidationResult → JSON Response
```

---

## Error Handling

### Tool Failures

- Each tool invocation is wrapped in `try/except`
- If a tool fails, the agent logs the error and continues with remaining tools
- Tool result is replaced with error message: `"<tool_name> unavailable: <error>"`

### LLM Failures

- If LLM invocation fails, the agent returns a basic validation result with:
  - `is_valid = False`
  - `summary = "Validation failed: <error>"`

### API Fallbacks

- **Routing**: MapBox → Google Maps → Geopy
- **Traffic**: MapBox → Time-based estimation
- **Weather**: Open-Meteo (no fallback, returns error on failure)

---

## Output Schema

### RouteValidationResult

```python
{
    "is_valid": bool,
    "issues": List[str],
    "recommendations": List[str],
    "action_plan": List[str],  # Deterministic 6-step plan
    "optimized_stop_order": Optional[List[str]],
    "summary": str,
    "estimated_duration_hours": Optional[float],
    "estimated_cost_usd": Optional[float]
}
```

### AgentRun (Database Model)

```python
{
    "route_slug": str,
    "audience_role": str,  # "dispatcher"
    "audience_experience": str,  # "advanced"
    "summary": str,
    "gemini_insight": str,  # Raw LLM output
    "recommended_actions": List[dict],  # Includes action_plan steps
    "tool_calls": List[dict],  # Tool invocations with outputs
    "rag_contexts": List[dict],  # Retrieved documents
    "used_gemini": bool,
    "created_at": datetime
}
```
