# Agent Architecture Documentation

## Overview

The Logistics Route Planner uses a **powerful LangChain-based AI agent** with real tool-calling capabilities, autonomous decision-making, and multi-source knowledge integration.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (React)                             │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐       │
│  │  Agent Panel   │  │ Planner Panel  │  │  Search Panel  │       │
│  │  (Chat UI)     │  │ (Route Plans)  │  │  (RAG Search)  │       │
│  └────────┬───────┘  └────────┬───────┘  └────────┬───────┘       │
└───────────┼──────────────────┼──────────────────┼─────────────────┘
            │                   │                   │
            │ POST /agent       │ POST /planner     │ POST /search
            ▼                   ▼                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      FASTAPI BACKEND                                 │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                    AGENT ROUTER                                 │ │
│  │  /api/agent/assess - Route readiness assessment                │ │
│  │  /api/agent/history - Historical agent runs                    │ │
│  └──────────────────┬──────────────────────────────────────────────┘ │
│                     │                                                 │
│                     ▼                                                 │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │              AGENT ORCHESTRATION LAYER                          │ │
│  │         (agent_langchain.py)                                    │ │
│  │                                                                  │ │
│  │  • run_route_readiness_agent()                                  │ │
│  │  • Creates AgentExecutor with tools                             │ │
│  │  • Manages tool selection and execution                         │ │
│  │  • Integrates RAG retrieval                                     │ │
│  │  • Parses and structures results                                │ │
│  └──────┬────────────────────┬────────────────────┬───────────────┘ │
│         │                    │                    │                  │
│         ▼                    ▼                    ▼                  │
│  ┌─────────────┐   ┌──────────────────┐   ┌──────────────┐        │
│  │  LLM        │   │  AGENT EXECUTOR  │   │  RAG         │        │
│  │  Provider   │   │  (LangChain)     │   │  Retriever   │        │
│  │             │   │                  │   │              │        │
│  │ • Gemini    │   │ • Tool calling   │   │ • FAISS      │        │
│  │   2.0 Flash │   │ • Reasoning loop │   │ • Embeddings │        │
│  │ • Groq      │   │ • Result parsing │   │ • Docs DB    │        │
│  │   (Llama3)  │   │ • Max 15 iters   │   │              │        │
│  └─────────────┘   └──────────────────┘   └──────────────┘        │
│                             │                                        │
│                             ▼                                        │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                     TOOL ECOSYSTEM                              │ │
│  │                  (agent_tools.py)                               │ │
│  │                                                                  │ │
│  │  ┌──────────────────────────────────────────────────────────┐  │ │
│  │  │         INTERNAL LOGISTICS TOOLS                          │  │ │
│  │  │                                                            │  │ │
│  │  │  🔧 fetch_route_brief()                                   │  │ │
│  │  │     • Get route details, audience, metrics                │  │ │
│  │  │                                                            │  │ │
│  │  │  🔧 fetch_delivery_window()                               │  │ │
│  │  │     • Deployment timeline, environment, freeze status     │  │ │
│  │  │                                                            │  │ │
│  │  │  🔧 fetch_support_contacts()                              │  │ │
│  │  │     • Team contacts, escalation channels                  │  │ │
│  │  │                                                            │  │ │
│  │  │  🔧 list_slo_watch_items()                                │  │ │
│  │  │     • Critical SLO metrics to monitor                     │  │ │
│  │  │                                                            │  │ │
│  │  │  🔧 calculate_route_metrics()                             │  │ │
│  │  │     • Speed, fuel, cost, driver breaks                    │  │ │
│  │  │                                                            │  │ │
│  │  │  🔧 check_weather_impact()                                │  │ │
│  │  │     • Weather conditions, delays, recommendations         │  │ │
│  │  └────────────────────────────────────────────────────────────┘  │ │
│  │                                                                  │ │
│  │  ┌──────────────────────────────────────────────────────────┐  │ │
│  │  │         EXTERNAL RESEARCH TOOLS                           │  │ │
│  │  │                                                            │  │ │
│  │  │  🌐 DuckDuckGo Search                                     │  │ │
│  │  │     • Real-time web search for logistics news/trends     │  │ │
│  │  │                                                            │  │ │
│  │  │  📚 Wikipedia Query                                       │  │ │
│  │  │     • Lookup logistics concepts and definitions          │  │ │
│  │  │                                                            │  │ │
│  │  │  📄 ArXiv Search (Optional)                               │  │ │
│  │  │     • Academic papers on logistics optimization          │  │ │
│  │  └────────────────────────────────────────────────────────────┘  │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                   KNOWLEDGE BASE                                │ │
│  │                                                                  │ │
│  │  • logistics_knowledge.txt                                      │ │
│  │  • fleet_management.txt                                         │ │
│  │  • dispatch_operations.txt                                      │ │
│  │                                                                  │ │
│  │  → Embedded with sentence-transformers                          │ │
│  │  → Stored in FAISS vector database                              │ │
│  │  → Retrieved via semantic similarity                            │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                  POSTGRESQL DATABASE                            │ │
│  │                                                                  │ │
│  │  • AgentRun history (assessments, tools used, insights)        │ │
│  │  • Document embeddings (FAISS index metadata)                  │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

## Agent Workflow

### 1. **Request Initiation**
```
User Input → Frontend → POST /api/agent/assess
```
Input includes:
- Route slug (e.g., "express-delivery")
- Launch date
- Audience role & experience level
- Risk analysis preference

### 2. **Agent Execution Flow**

```mermaid
graph TD
    A[Request Received] --> B[Initialize LLM Provider]
    B --> C[Load All Tools]
    C --> D[Create Agent with Tools]
    D --> E[Execute RAG Retrieval]
    E --> F[Agent Planning Phase]
    
    F --> G{Tool Selection}
    G -->|Route Info| H[fetch_route_brief]
    G -->|Timeline| I[fetch_delivery_window]
    G -->|Contacts| J[fetch_support_contacts]
    G -->|SLOs| K[list_slo_watch_items]
    G -->|Calculations| L[calculate_route_metrics]
    G -->|Weather| M[check_weather_impact]
    G -->|Research| N[DuckDuckGo Search]
    G -->|Concepts| O[Wikipedia Query]
    
    H --> P[Tool Results]
    I --> P
    J --> P
    K --> P
    L --> P
    M --> P
    N --> P
    O --> P
    
    P --> Q{More Info Needed?}
    Q -->|Yes| G
    Q -->|No| R[Generate Assessment]
    
    R --> S[Parse Recommendations]
    S --> T[Build Route Plan]
    T --> U[Store in Database]
    U --> V[Return Result to User]
```

### 3. **Tool Selection Process**

The agent **autonomously decides** which tools to use based on:
- User query content
- Current context
- Tool descriptions
- Previous tool results

Example decision tree:
```
User asks: "Is express-delivery ready for launch on Jan 15?"

Agent thinks:
1. Need route details → calls fetch_route_brief("express-delivery")
2. Need timeline → calls fetch_delivery_window("express-delivery")
3. Notices SLO requirements → calls list_slo_watch_items("express-delivery")
4. Wants industry context → calls DuckDuckGo Search("express delivery best practices 2025")
5. Has enough info → generates assessment
```

### 4. **RAG Integration**

```
Query: "Express Delivery Route Driver delivery logistics"
         ↓
    Embedding Model (sentence-transformers)
         ↓
    Vector Search in FAISS
         ↓
    Top 3 Most Relevant Documents
         ↓
    Injected into Agent Context
```

### 5. **Result Generation**

The agent produces:
1. **Summary**: Brief overview of route status
2. **AI Insight**: Strategic assessment from LLM
3. **Recommendations**: Actionable items with priorities
4. **Route Plan**: Structured implementation plan
5. **Tool Trace**: Which tools were called and why
6. **RAG Contexts**: Relevant documents used

## Tool Descriptions

### Internal Tools

| Tool | Purpose | Input | Output |
|------|---------|-------|--------|
| `fetch_route_brief` | Get route specifications | route_slug | JSON: name, summary, audience, metrics |
| `fetch_delivery_window` | Get deployment timeline | route_slug | JSON: dates, environment, freeze status |
| `fetch_support_contacts` | Get team contacts | audience_role | JSON: contacts, escalation channels |
| `list_slo_watch_items` | Get critical SLOs | route_slug | JSON: SLO items requiring monitoring |
| `calculate_route_metrics` | Calculate performance metrics | route_slug, distance, hours | JSON: speed, fuel, cost, breaks |
| `check_weather_impact` | Assess weather impact | location, date | JSON: conditions, impact level, recommendations |

### External Tools

| Tool | Purpose | Use Case |
|------|---------|----------|
| **DuckDuckGo Search** | Web search | Latest logistics trends, news, best practices |
| **Wikipedia** | Concept lookup | Definitions, logistics terminology |
| **ArXiv** (optional) | Academic research | Optimization algorithms, research papers |

## Key Features

### 1. **Autonomous Tool Usage**
- Agent decides which tools to call
- No hardcoded tool sequences
- Dynamic reasoning based on context

### 2. **Multi-Source Knowledge**
- Internal data (routes, contacts, SLOs)
- Vector database (RAG documents)
- Web search (real-time information)
- Wikipedia (reference knowledge)

### 3. **Iterative Reasoning**
- Up to 15 iterations allowed
- Agent can chain tool calls
- Refines understanding with each tool result

### 4. **Error Handling**
- Parse error recovery
- Tool failure graceful degradation
- Comprehensive logging

### 5. **Traceability**
- Every tool call recorded
- Input arguments logged
- Output previews stored
- Full audit trail in database

## Technology Stack

### Core Framework
- **LangChain**: Agent orchestration, tool calling
- **LangGraph**: Advanced agent workflows (optional)

### LLM Providers
- **Google Gemini 2.0 Flash**: Primary LLM
- **Groq (Llama3)**: Fallback LLM via OpenAI API

### Vector Database
- **FAISS**: Fast similarity search
- **sentence-transformers**: Text embeddings

### Search Tools
- **duckduckgo-search**: Web search
- **wikipedia-api**: Wikipedia integration
- **arxiv**: Academic papers
- **tavily**: Advanced web search (optional)

### Backend
- **FastAPI**: REST API framework
- **PostgreSQL**: Persistent storage
- **SQLAlchemy**: ORM
- **Alembic**: Database migrations

## Configuration

### Environment Variables

```bash
# LLM Provider (choose one or both)
GEMINI_API_KEY=your-gemini-key
GROQ_API_KEY=your-groq-key

# Optional: Model selection
GEMINI_MODEL=gemini-2.0-flash
GROQ_MODEL=llama3-8b-8192

# Optional: Advanced search
TAVILY_API_KEY=your-tavily-key

# Database
DATABASE_URL=postgresql://user:pass@localhost/logistics
```

### Agent Parameters

In [agent_langchain.py](backend/app/services/agent_langchain.py#L140):
```python
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,              # Enable logging
    max_iterations=15,         # Max reasoning steps
    handle_parsing_errors=True,# Recover from parse errors
    return_intermediate_steps=True,  # Return tool trace
)
```

## Usage Example

### Request
```json
POST /api/agent/assess
{
  "route_slug": "express-delivery",
  "launch_date": "2025-01-15",
  "audience_role": "Driver",
  "audience_experience": "intermediate",
  "include_risks": true
}
```

### Agent Process
```
1. 🤖 Agent initialized with 8 tools
2. 🔍 RAG search: "Express Delivery Route Driver delivery logistics"
   → Retrieved 3 documents
3. 🔧 Tool: fetch_route_brief("express-delivery")
   → Got: "Optimized same-day delivery routes..."
4. 🔧 Tool: fetch_delivery_window("express-delivery")
   → Got: "Jan 15-17, Production, Freeze required"
5. 🔧 Tool: list_slo_watch_items("express-delivery")
   → Got: "Route latency <500ms, GPS updates 30s..."
6. 🌐 Tool: DuckDuckGo Search("same day delivery optimization 2025")
   → Got: "Latest trends in express delivery..."
7. 💭 Agent reasoning: "Launch ready but need monitoring plan"
8. ✅ Generated 4 recommendations with priorities
```

### Response
```json
{
  "summary": "Express Delivery Route targets Driver personas...",
  "gemini_insight": "Route is technically ready for Jan 15 launch...",
  "recommended_actions": [
    {
      "title": "[AI Agent] Implement real-time GPS monitoring",
      "detail": "Critical for 30-second update SLO",
      "priority": "high"
    },
    ...
  ],
  "tool_calls": [
    {"tool": "fetch_route_brief", "arguments": {...}, "output_preview": "..."},
    {"tool": "fetch_delivery_window", "arguments": {...}, "output_preview": "..."},
    ...
  ],
  "rag_contexts": [...]
}
```

## Extending the Agent

### Adding New Tools

1. **Create tool function in `agent_tools.py`**:
```python
@tool
def check_fleet_availability(date_str: str, region: str) -> str:
    """Check vehicle availability for a specific date and region."""
    # Implementation
    return json.dumps(result)
```

2. **Add to tool list in `get_all_tools()`**:
```python
def get_all_tools():
    internal_tools = [
        fetch_route_brief,
        # ... existing tools
        check_fleet_availability,  # Add here
    ]
    # ...
```

3. **Agent automatically uses it!**
   - No changes needed in agent code
   - Tool is available via description
   - Agent decides when to call it

### Adding External APIs

Example: Weather API integration
```python
@tool
def fetch_real_weather(location: str, date_str: str) -> str:
    """Fetch real weather forecast from weather API."""
    import requests
    
    api_key = os.getenv("WEATHER_API_KEY")
    response = requests.get(
        f"https://api.weather.com/forecast",
        params={"location": location, "date": date_str, "key": api_key}
    )
    return json.dumps(response.json())
```

## Performance Considerations

- **Average response time**: 5-15 seconds
- **Tool calls per request**: 3-8 typically
- **LLM tokens**: ~2000-5000 per request
- **Database queries**: 1-5 per request

## Monitoring

Track in database:
- Tool usage frequency
- Average iterations per request
- Success/failure rates
- Token consumption
- Response times

Query example:
```sql
SELECT 
  tool_calls->>'tool' as tool_name,
  COUNT(*) as usage_count
FROM agent_runs
GROUP BY tool_name
ORDER BY usage_count DESC;
```

## Future Enhancements

1. **Custom Tool Development**
   - Fleet management API integration
   - Real-time traffic data
   - Customer feedback analysis

2. **Advanced Agent Patterns**
   - Multi-agent collaboration
   - Hierarchical task decomposition
   - Memory and learning

3. **Performance Optimization**
   - Tool result caching
   - Parallel tool execution
   - Streaming responses

4. **Enhanced Observability**
   - LangSmith integration
   - Token usage tracking
   - A/B testing frameworks
