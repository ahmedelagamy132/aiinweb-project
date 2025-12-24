# 🚚 AI-Powered Logistics Route Planner

## What is This System?

The **AI-Powered Logistics Route Planner** is an intelligent web application designed to help logistics dispatchers and fleet managers plan, validate, and optimize delivery routes using artificial intelligence. The system combines interactive map-based route planning with AI-powered analysis to ensure routes are efficient, feasible, and optimized for real-world conditions.

### Primary Use Cases

- **Route Planning**: Interactively create delivery routes by clicking on a map to set start points and delivery stops
- **Intelligent Validation**: AI agent validates routes against multiple constraints (timing, weather, traffic, vehicle capacity)
- **Route Optimization**: Automatically optimize stop sequences to reduce travel time and fuel consumption
- **Real-time Analysis**: Get AI-generated insights on weather impacts, traffic conditions, and potential issues
- **Decision Support**: Receive actionable recommendations from AI to improve route efficiency and reliability

### Who Uses This System?

- **Dispatchers**: Plan daily delivery routes and assign them to drivers
- **Fleet Managers**: Optimize fleet operations and monitor route performance
- **Logistics Coordinators**: Ensure timely deliveries while managing constraints
- **Operations Teams**: Make data-driven decisions about route feasibility

---

## 🏗️ System Architecture

### High-Level Overview

```
┌─────────────────┐
│   React UI      │  ← User interacts with map
│   (Frontend)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   FastAPI       │  ← REST API endpoints
│   (Backend)     │
└────────┬────────┘
         │
         ├──────────────────┬─────────────────┬──────────────────┐
         ▼                  ▼                 ▼                  ▼
┌─────────────┐    ┌──────────────┐   ┌─────────────┐   ┌──────────────┐
│  LangChain  │    │   AI Tools   │   │     RAG     │   │  PostgreSQL  │
│   Agent     │    │  (5 tools)   │   │   System    │   │   Database   │
└─────────────┘    └──────────────┘   └─────────────┘   └──────────────┘
```

### Technology Stack

**Frontend**
- React 18.3.1 - Modern UI framework
- Leaflet 4.2.1 - Interactive mapping library
- Vite 5.4.21 - Fast build tool with HMR
- React-Leaflet - React bindings for Leaflet maps

**Backend**
- Python 3.11 - Core language
- FastAPI - High-performance API framework
- LangChain - AI agent orchestration
- Pydantic 2.x - Data validation and serialization

**AI/ML**
- Gemini 2.0 Flash - Primary LLM (Google)
- Groq (llama3-8b-8192) - Fallback LLM
- FAISS - Vector database for RAG
- Sentence Transformers - Text embeddings

**Infrastructure**
- Docker & Docker Compose - Containerization
- PostgreSQL - Persistent data storage
- Nginx - Reverse proxy and load balancing
- Alembic - Database migrations

---

## 🤖 AI Agent System

### What is the Agent?

The AI Agent is the intelligent core of the system, powered by **LangChain** and large language models (LLMs). It acts as an autonomous decision-maker that:

1. **Analyzes** route requests with multiple parameters
2. **Decides** which tools to use and when to use them
3. **Executes** tools to gather real-world data (weather, traffic, metrics)
4. **Reasons** about the collected information
5. **Generates** comprehensive validation reports with recommendations

### How the Agent Works

#### Autonomous Tool Calling
Unlike traditional rule-based systems, the agent **decides dynamically** which tools to call based on the route context:

```python
# Agent reasoning process (simplified)
Agent: "User wants to validate a route with 5 stops..."
Agent: "I should check weather first" → Calls check_weather_conditions
Agent: "Now I need to calculate distances" → Calls calculate_route_metrics
Agent: "Are the time windows feasible?" → Calls validate_route_timing
Agent: "Can I optimize the sequence?" → Calls optimize_stop_sequence
Agent: "Finally, check traffic" → Calls check_traffic_conditions
Agent: "I have enough information now, generating report..."
```

#### Agent Configuration

**LLM Providers** (automatic fallback):
- **Primary**: Gemini 2.0 Flash (temperature=0.7 for creativity)
- **Fallback**: Groq with llama3-8b-8192

**Agent Executor Settings**:
- Maximum iterations: 15 (prevents infinite loops)
- Tool selection: Autonomous (agent decides)
- Error handling: Graceful degradation
- Traceability: Full audit logs

### Agent Capabilities

| Capability | Description |
|-----------|-------------|
| **Multi-tool Orchestration** | Calls 5+ different tools in optimal sequence |
| **Contextual RAG** | Retrieves relevant logistics knowledge from vector DB |
| **Constraint Validation** | Checks time windows, vehicle capacity, shift hours |
| **Weather Analysis** | Assesses weather impact on route feasibility |
| **Traffic Awareness** | Considers traffic patterns at different times |
| **Route Optimization** | Suggests optimal stop sequences |
| **Natural Language Output** | Generates human-readable reports |
| **Persistent Memory** | Stores all agent runs in database |

---

## 🛠️ AI Tools System

The agent has access to **5 specialized tools** that provide real-world data and calculations. Each tool is a Python function decorated with `@tool` from LangChain.

### Tool 1: check_weather_conditions
**Purpose**: Check weather conditions for a specific location

**Input Parameters**:
```python
{
    "location": "San Francisco, CA"  # City name or address
}
```

**Output**:
```json
{
    "location": "San Francisco, CA",
    "current_conditions": "partly cloudy",
    "temperature_celsius": 18,
    "precipitation_chance": 20,
    "wind_speed_kmh": 15,
    "visibility_km": 10,
    "alert_level": "normal",
    "recommendation": "Conditions are favorable for deliveries"
}
```

**When Agent Uses It**: 
- Route involves outdoor deliveries
- Weather-sensitive cargo
- Long-distance routes

---

### Tool 2: calculate_route_metrics
**Purpose**: Calculate total distance and estimated time for a route

**Input Parameters**:
```python
{
    "route_data": {
        "start_location": "123 Main St",
        "stops": [
            {"stop_id": "S001", "location": "456 Oak Ave"},
            {"stop_id": "S002", "location": "789 Pine St"}
        ],
        "vehicle_type": "van"
    }
}
```

**Output**:
```json
{
    "estimated_time_hours": 3.5,
    "distance_km": 45.2,
    "fuel_estimate_liters": 8.5,
    "toll_estimate_usd": 5.0,
    "breakdown": {
        "driving_time_hours": 2.8,
        "service_time_hours": 0.7
    }
}
```

**When Agent Uses It**:
- Calculate if route fits within shift hours
- Estimate fuel costs
- Compare multiple route options

---

### Tool 3: validate_route_timing
**Purpose**: Validate if route can be completed within time constraints

**Input Parameters**:
```python
{
    "route_request": {
        "route_id": "R001",
        "start_location": "Warehouse A",
        "planned_start_time": "2025-01-15T08:00:00Z",
        "planned_end_time": "2025-01-15T17:00:00Z",
        "stops": [
            {
                "stop_id": "S001",
                "location": "123 Main St",
                "time_window_start": "09:00",
                "time_window_end": "12:00",
                "service_duration_minutes": 15
            }
        ]
    }
}
```

**Output**:
```json
{
    "is_valid": true,
    "issues": [],
    "warnings": ["Tight schedule at stop S003"],
    "total_duration_hours": 7.5,
    "buffer_time_minutes": 30,
    "recommendations": [
        "Start 15 minutes earlier to add buffer",
        "Consider traffic at stop S002 around 3 PM"
    ]
}
```

**When Agent Uses It**:
- Validate delivery time windows
- Check shift hour compliance
- Identify scheduling conflicts

---

### Tool 4: optimize_stop_sequence
**Purpose**: Find the optimal order of stops to minimize travel time

**Input Parameters**:
```python
{
    "route_request": {
        "route_id": "R001",
        "start_location": "Warehouse",
        "stops": [
            {"stop_id": "S001", "location": "Downtown"},
            {"stop_id": "S002", "location": "Suburb North"},
            {"stop_id": "S003", "location": "Industrial Park"}
        ]
    }
}
```

**Output**:
```json
{
    "optimized": true,
    "original_sequence": ["S001", "S002", "S003"],
    "optimized_sequence": ["S002", "S001", "S003"],
    "estimated_improvement": "10-15% reduction in backtracking",
    "reasoning": "Reordered to follow geographic proximity pattern"
}
```

**When Agent Uses It**:
- User requests route optimization
- Detect inefficient stop sequences
- Suggest improvements

---

### Tool 5: check_traffic_conditions
**Purpose**: Check traffic conditions at specific time and location

**Input Parameters**:
```python
{
    "location": "Downtown Los Angeles",
    "time_of_day": "17:30"  # 24-hour format
}
```

**Output**:
```json
{
    "location": "Downtown Los Angeles",
    "time_of_day": "17:30",
    "traffic_level": "heavy",
    "delay_factor": 1.5,
    "estimated_delay_minutes": 20,
    "recommendation": "Consider alternative route or earlier departure",
    "peak_hours": ["07:00-09:00", "16:30-18:30"]
}
```

**When Agent Uses It**:
- Routes during rush hours
- Urban delivery areas
- Time-critical deliveries

---

### Tool Invocation Pattern

All tools use the **LangChain `.invoke()` method** with Pydantic-validated parameters:

```python
# Example: Agent calling a tool
result = check_weather_conditions.invoke({
    "location": "San Francisco, CA"
})

# Tool returns JSON string
weather_data = json.loads(result)
```

### Tool Error Handling

Each tool has built-in error handling:
- Returns descriptive error messages instead of crashing
- Provides fallback values when APIs are unavailable
- Logs errors for debugging

---

## 📚 RAG System (Retrieval-Augmented Generation)

### What is RAG?

**RAG** combines document retrieval with AI generation to provide context-aware responses. The system retrieves relevant logistics knowledge from a vector database and feeds it to the LLM for better decision-making.

### How RAG Works in This System

```
┌─────────────────┐
│  User Query     │  "Validate route with 5 stops in SF"
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Text Embedding  │  Convert query to vector
│  (Sentence      │  [0.23, -0.15, 0.48, ...]
│  Transformers)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  FAISS Search   │  Find similar documents
│ (Vector Store)  │  Top 3 matches by cosine similarity
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Documents     │  • Fleet management best practices
│   Retrieved     │  • Dispatch operations guidelines
│                 │  • Logistics optimization strategies
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  LLM Context    │  Combine retrieved docs + tool results
│  Enhancement    │  → Generate informed response
└─────────────────┘
```

### RAG Components

#### 1. Document Store
Located in `backend/data/`:
- **fleet_management.txt** - Vehicle types, capacity, maintenance schedules
- **dispatch_operations.txt** - Best practices for route planning and dispatching
- **logistics_knowledge.txt** - General logistics domain knowledge

#### 2. Vector Database (FAISS)
- **Storage**: In-memory vector store (persisted to disk)
- **Embeddings**: Sentence transformers (all-MiniLM-L6-v2)
- **Similarity**: Cosine similarity for document retrieval
- **Top-K**: Retrieves 3 most relevant documents per query

#### 3. Document Ingestion
```bash
# Initialize RAG system
python backend/ingest_documents.py

# What it does:
# 1. Reads .txt files from backend/data/
# 2. Splits documents into chunks
# 3. Generates embeddings for each chunk
# 4. Stores in FAISS index
# 5. Saves index to disk for persistence
```

#### 4. Query Flow
```python
# In agent execution
query = "Route validation for urban deliveries"
rag_contexts = rag_system.semantic_search(query, k=3)

# Returns:
[
    RAGContext(
        content="When planning urban routes, consider traffic...",
        source="dispatch_operations.txt",
        score=0.87
    ),
    RAGContext(
        content="Fleet vehicles should be matched to cargo type...",
        source="fleet_management.txt", 
        score=0.82
    ),
    # ... more contexts
]
```

### RAG Benefits

- **Contextual Intelligence**: Agent knows logistics best practices
- **Domain Expertise**: Incorporates company-specific policies
- **Consistent Guidance**: Same knowledge base for all queries
- **Extensible**: Add new documents without code changes
- **Transparent**: Shows source documents in responses

---

## 🗺️ Frontend - Interactive Map Interface

### Key Features

#### 1. Map-Based Route Creation
- **Start Point Selection**: Click map to set route start location (green marker)
- **Delivery Stops**: Click to add stops (blue markers with labels)
- **Interactive Markers**: Drag to reposition, click to edit details
- **Location Search**: Reverse geocoding shows addresses

#### 2. Route Configuration Panel
**Start Point Section**:
- Location address display
- Planned start time picker (default: 08:00)
- Planned end time picker (shift hours)

**Delivery Stops Section**:
- Stop name input
- Time window start/end
- Service duration (minutes)
- Priority level
- Special instructions
- Remove stop button

**Vehicle Selection**:
- Van, Truck, Motorcycle options
- Vehicle capacity display

#### 3. Validation Results Display

**Layout**: Results appear below map (full width) for better visibility

**Sections**:
- ✅ **Validation Status**: Pass/Fail with color coding
- 🔴 **Issues**: Critical problems that must be fixed (red box)
- 💡 **Recommendations**: AI suggestions for improvement (blue box)
- 📊 **Metrics**: Distance, duration, fuel estimates (gray cards)
- ✨ **Optimized Stop Order**: AI-suggested sequence (green box)
- 🛠️ **Tools Used**: All AI tools executed with inputs/outputs

#### 4. Real-time Validation
Click **"Validate Route with AI"** button to:
1. Send route data to backend
2. Agent executes tools and analyzes
3. Display comprehensive report in 2-3 seconds

### Component Structure

```
frontend/src/
├── App.jsx                    # Main application
├── components/
│   └── NavBar.jsx            # Top navigation
└── features/
    ├── agent/
    │   ├── components/
    │   │   └── AgentPanel.jsx    # Route planning interface
    │   └── hooks/
    │       └── useAgent.js        # Agent API calls
    ├── chatbot/
    │   └── components/
    │       └── ChatbotPanel.jsx   # Chat interface
    └── planner/
        └── components/
            └── PlannerPanel.jsx   # (Legacy) Basic planner
```

### State Management

```jsx
// AgentPanel.jsx
const [startPoint, setStartPoint] = useState(null);  // {lat, lng, location}
const [stops, setStops] = useState([]);              // Array of delivery stops
const [result, setResult] = useState(null);          // Validation result
const [loading, setLoading] = useState(false);       // Loading state
```

---

## 🔌 Backend API Endpoints

### Route Planning API

#### POST `/api/agent/validate-route`
Validate and optimize a route using AI agent

**Request Body**:
```json
{
  "route_id": "R001",
  "start_location": "123 Main St, San Francisco, CA",
  "planned_start_time": "2025-01-15T08:00:00Z",
  "planned_end_time": "2025-01-15T17:00:00Z",
  "vehicle_id": "VAN-001",
  "vehicle_type": "van",
  "stops": [
    {
      "stop_id": "S001",
      "location": "456 Oak Ave, San Francisco, CA",
      "time_window_start": "09:00",
      "time_window_end": "12:00",
      "service_duration_minutes": 15,
      "priority": "high",
      "special_instructions": "Ring doorbell"
    }
  ],
  "constraints": {
    "max_driving_hours": 8,
    "require_signature": true
  },
  "task": "validate_and_optimize"
}
```

**Response**:
```json
{
  "is_valid": true,
  "issues": [],
  "recommendations": [
    "Start 15 minutes earlier to add buffer time",
    "Consider traffic at stop S002 around 3 PM"
  ],
  "optimized_stop_order": ["S002", "S001", "S003"],
  "summary": "Route is valid with 5 stops. Estimated duration: 7.2h. 2 recommendations provided.",
  "estimated_duration_hours": 7.2,
  "estimated_distance_km": 98.5,
  "tool_calls": [
    {
      "name": "check_weather_conditions",
      "args": {"location": "San Francisco, CA"},
      "output": "{\"temperature\": 18, \"alert_level\": \"normal\"}"
    }
  ]
}
```

### Chat API

#### POST `/api/chat/message`
Send message to logistics chatbot

**Request Body**:
```json
{
  "message": "What's the weather like for my route?",
  "history": []
}
```

**Response**:
```json
{
  "response": "The weather conditions for San Francisco are partly cloudy with 18°C temperature. Conditions are favorable for deliveries.",
  "sources": ["weather_api", "dispatch_operations.txt"]
}
```

### Other Endpoints

- `GET /api/agent/history` - Get agent execution history
- `POST /api/planner/optimize` - Basic route optimization
- `GET /api/echo` - Health check endpoint

---

## 💾 Database Schema

### AgentRun Table
Stores all AI agent executions for audit and analysis

```sql
CREATE TABLE agent_runs (
    id SERIAL PRIMARY KEY,
    route_slug VARCHAR(255),
    query_text TEXT,
    agent_output TEXT,
    tool_calls JSONB,
    rag_contexts JSONB,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    execution_time_ms INTEGER
);
```

**Sample Record**:
```json
{
  "id": 1,
  "route_slug": "R001",
  "query_text": "Validate route with 5 stops in San Francisco",
  "agent_output": "VALID: true\nISSUE: None\nRECOMMENDATION: Start earlier...",
  "tool_calls": [
    {"tool": "check_weather_conditions", "result": "..."}
  ],
  "rag_contexts": [
    {"content": "Best practices...", "source": "dispatch_operations.txt"}
  ],
  "execution_time_ms": 2340,
  "created_at": "2025-01-15T10:23:45Z"
}
```

---

## 🚀 Getting Started

### Prerequisites

- Docker Desktop 20.10+
- Docker Compose 2.0+
- API Keys:
  - **Required**: Gemini API key OR Groq API key
  - Optional: Tavily API key (for web search)

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd logistics-route-planner
```

2. **Set up environment variables**
```bash
# Copy template
cp backend/env-template.txt backend/.env

# Edit backend/.env
GEMINI_API_KEY=your_gemini_key_here
# OR
GROQ_API_KEY=your_groq_key_here

# Database (already configured)
DATABASE_URL=postgresql://user:password@db:5432/logistics
```

3. **Initialize RAG system**
```bash
docker-compose run --rm backend python ingest_documents.py
```

4. **Start the system**
```bash
docker-compose up --build
```

5. **Access the application**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Quick Test

1. Open http://localhost:3000
2. Navigate to "AI Agent" tab
3. Click on map to set start point (green marker appears)
4. Click multiple times to add delivery stops
5. Fill in stop details (name, time windows)
6. Click "Validate Route with AI"
7. View validation results below map

---

## 📊 System Monitoring

### Backend Logs

**View real-time logs**:
```bash
docker logs -f logistics-route-planner-backend-1
```

**What to look for**:
```
🤖 Agent initialized with 5 tools
🔍 RAG search completed: 3 documents retrieved
🔧 Tool call: check_weather_conditions → SUCCESS
🔧 Tool call: calculate_route_metrics → SUCCESS
✨ Agent output: VALID: true...
💾 Agent run saved to database (ID: 42)
```

### Performance Metrics

| Metric | Typical Value |
|--------|---------------|
| Agent execution time | 2-4 seconds |
| Tool call latency | 100-300ms each |
| RAG retrieval time | 50-100ms |
| Database save time | 10-20ms |
| Total response time | 2.5-5 seconds |

### Error Handling

**Graceful degradation**:
- If weather tool fails → Continue with warning
- If RAG unavailable → Use only tool results
- If LLM times out → Return cached response
- If all tools fail → Return basic validation

---

## 🔧 Configuration

### Agent Configuration
`backend/app/services/agent_langchain.py`

```python
# LLM settings
temperature = 0.7           # Creativity (0.0-1.0)
max_tokens = 2000          # Response length
timeout = 30               # Seconds

# Agent executor
max_iterations = 15        # Max tool calling rounds
early_stopping = True      # Stop when done
```

### Tool Configuration
`backend/app/services/agent_tools.py`

```python
# Tool behavior
WEATHER_SIMULATION = True   # Use simulated weather (no API key needed)
TRAFFIC_CACHE_TTL = 300    # Cache traffic data (seconds)
METRICS_PRECISION = 2      # Decimal places for calculations
```

### RAG Configuration
`backend/app/services/rag.py`

```python
# Vector search
TOP_K = 3                  # Documents to retrieve
CHUNK_SIZE = 500           # Characters per chunk
CHUNK_OVERLAP = 50         # Overlap between chunks
SIMILARITY_THRESHOLD = 0.5 # Min similarity score
```

---

## 🧪 Testing

### Manual Testing

**Test Route Validation**:
```bash
curl -X POST http://localhost:8000/api/agent/validate-route \
  -H "Content-Type: application/json" \
  -d '{
    "route_id": "TEST-001",
    "start_location": "San Francisco, CA",
    "planned_start_time": "2025-01-15T08:00:00Z",
    "planned_end_time": "2025-01-15T17:00:00Z",
    "stops": [
      {
        "stop_id": "S001",
        "location": "Oakland, CA",
        "time_window_start": "09:00",
        "time_window_end": "12:00",
        "service_duration_minutes": 15
      }
    ],
    "task": "validate_and_optimize"
  }'
```

### Unit Tests

```bash
# Run backend tests
docker-compose run --rm backend pytest

# Run specific test
docker-compose run --rm backend pytest tests/test_agent_tools.py
```

### Test Scenarios

1. **Simple Route**: 2 stops, no constraints → Should pass validation
2. **Time Conflict**: Overlapping time windows → Should detect issue
3. **Long Route**: 10+ stops → Should optimize sequence
4. **Bad Weather**: Route during storm conditions → Should warn
5. **Rush Hour**: Route during peak traffic → Should suggest delays

---

## 📈 Future Enhancements

### Planned Features

- [ ] **Real-time GPS tracking** integration
- [ ] **Multi-vehicle routing** (fleet optimization)
- [ ] **Dynamic re-routing** based on traffic
- [ ] **Historical route analytics** dashboard
- [ ] **Driver mobile app** integration
- [ ] **Automated dispatch** scheduling
- [ ] **Cost optimization** (fuel, tolls, time)
- [ ] **Customer notification** system
- [ ] **Real weather API** integration (OpenWeatherMap)
- [ ] **Real traffic API** integration (Google Maps)

### Extensibility

**Adding new tools**:
```python
# backend/app/services/agent_tools.py

@tool
def check_vehicle_availability(vehicle_id: str) -> str:
    """Check if a vehicle is available for assignment."""
    # Your implementation
    return json.dumps({"available": True})

# Tool automatically available to agent!
```

**Adding new documents to RAG**:
```bash
# Add .txt file to backend/data/
echo "New logistics knowledge..." > backend/data/new_guide.txt

# Re-ingest
docker-compose run --rm backend python ingest_documents.py
```

---

## 🤝 Contributing

### Development Workflow

1. Create feature branch
2. Make changes
3. Test locally with Docker
4. Submit pull request

### Code Style

- **Python**: PEP 8, type hints required
- **JavaScript**: ESLint configuration
- **Commits**: Conventional commits format

---

## 📄 License

MIT License

---

## 🆘 Support & Troubleshooting

### Common Issues

**Issue**: "Agent execution timeout"
- **Solution**: Increase timeout in config or check LLM API key

**Issue**: "RAG documents not found"
- **Solution**: Run `python ingest_documents.py` to initialize

**Issue**: "Map not loading"
- **Solution**: Check browser console, verify Leaflet CDN

**Issue**: "Tool execution failed"
- **Solution**: Check backend logs for specific tool error

### Getting Help

- Check [API_ENDPOINTS_GUIDE.md](API_ENDPOINTS_GUIDE.md) for API details
- See [AGENT_DIAGRAM.md](AGENT_DIAGRAM.md) for architecture diagrams
- Review [AGENT_USAGE_GUIDE.md](AGENT_USAGE_GUIDE.md) for usage instructions

---

**Built with ❤️ using LangChain, FastAPI, and React**
