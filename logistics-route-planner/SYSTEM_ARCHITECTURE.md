# Logistics Route Planner - System Architecture

## 🏗️ System Overview

This document explains the complete architecture of the Logistics Route Planner system.

## 📊 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                          USER INTERFACE                              │
│                      (React + Vite Frontend)                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐           │
│  │  Agent   │  │ Planner  │  │  Search  │  │ History  │           │
│  │  Panel   │  │  Panel   │  │  Panel   │  │  Panel   │           │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘           │
└──────────────────────────┬───────────────────────────────────────────┘
                           │ HTTP Requests (/api/*)
                           ↓
┌─────────────────────────────────────────────────────────────────────┐
│                          NGINX PROXY                                 │
│                         (Port 8080)                                  │
│  • Routes /api/* → Backend                                           │
│  • Routes /* → Frontend                                              │
└──────────────────────────┬───────────────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      BACKEND API SERVER                              │
│                   (FastAPI + Python 3.11)                            │
│                         Port 8000                                    │
│                                                                       │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                    API ROUTERS                                 │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐     │  │
│  │  │  Agent   │  │ Planner  │  │  Gemini  │  │   Echo   │     │  │
│  │  │ Router   │  │  Router  │  │  Router  │  │  Router  │     │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘     │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                           ↓                                           │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                    SERVICES LAYER                              │  │
│  │                                                                 │  │
│  │  ┌─────────────────────────────────────────────────────────┐  │  │
│  │  │            AI AGENT SERVICE                             │  │  │
│  │  │  (LangChain + Groq/Gemini)                              │  │  │
│  │  │                                                           │  │  │
│  │  │  ┌────────────────────────────────────────────────┐     │  │  │
│  │  │  │  1. Route Context Gathering (Tools)            │     │  │  │
│  │  │  │     • get_route_info()                          │     │  │  │
│  │  │  │     • get_delivery_window()                     │     │  │  │
│  │  │  │     • get_contact_info()                        │     │  │  │
│  │  │  └────────────────────────────────────────────────┘     │  │  │
│  │  │                        ↓                                  │  │  │
│  │  │  ┌────────────────────────────────────────────────┐     │  │  │
│  │  │  │  2. RAG Retrieval (Automatic)                  │     │  │  │
│  │  │  │     • Embed query with SentenceTransformers    │     │  │  │
│  │  │  │     • FAISS similarity search                   │     │  │  │
│  │  │  │     • Retrieve top-k documents                  │     │  │  │
│  │  │  └────────────────────────────────────────────────┘     │  │  │
│  │  │                        ↓                                  │  │  │
│  │  │  ┌────────────────────────────────────────────────┐     │  │  │
│  │  │  │  3. LLM Analysis (Gemini/Groq)                 │     │  │  │
│  │  │  │     • Generate route readiness assessment       │     │  │  │
│  │  │  │     • Create recommendations                    │     │  │  │
│  │  │  │     • Identify risks and blockers               │     │  │  │
│  │  │  └────────────────────────────────────────────────┘     │  │  │
│  │  └─────────────────────────────────────────────────────────┘  │  │
│  │                                                                 │  │
│  │  ┌─────────────────────────────────────────────────────────┐  │  │
│  │  │            PLANNER SERVICE                              │  │  │
│  │  │  (AI-Powered Route Planning)                            │  │  │
│  │  │                                                           │  │  │
│  │  │  • Groq/Gemini LLM for plan generation                  │  │  │
│  │  │  • Validation of route parameters                       │  │  │
│  │  │  • Fallback to rule-based templates                     │  │  │
│  │  └─────────────────────────────────────────────────────────┘  │  │
│  │                                                                 │  │
│  │  ┌─────────────────────────────────────────────────────────┐  │  │
│  │  │            RAG SERVICE                                  │  │  │
│  │  │  (Knowledge Base Search)                                │  │  │
│  │  │                                                           │  │  │
│  │  │  Components:                                             │  │  │
│  │  │  • SentenceTransformers (all-MiniLM-L6-v2)             │  │  │
│  │  │  • FAISS IndexFlatL2 (384-dim vectors)                 │  │  │
│  │  │  • Document chunking with overlap                       │  │  │
│  │  │                                                           │  │  │
│  │  │  Two Usage Modes:                                        │  │  │
│  │  │  1. Automatic (in agent pipeline)                       │  │  │
│  │  │  2. Interactive (via /ai/search endpoint)               │  │  │
│  │  └─────────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                           ↓                                           │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                    DATA LAYER                                  │  │
│  │  • SQLAlchemy ORM                                              │  │
│  │  • Alembic migrations                                          │  │
│  │  • Models: AgentRun, Route, DocumentChunk                     │  │
│  └───────────────────────────────────────────────────────────────┘  │
└──────────────────────────┬────────────────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      DATABASE SERVER                                 │
│                      (PostgreSQL 16)                                 │
│                                                                       │
│  Tables:                                                              │
│  • agent_runs          → Historical agent executions                 │
│  • routes              → Route metadata and configurations           │
│  • document_chunks     → Embedded knowledge base (30 chunks)         │
│                           - id, content, source, embedding (384-dim) │
│                                                                       │
│  Indexes:                                                             │
│  • FAISS vector index for similarity search                          │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                    EXTERNAL AI SERVICES                              │
│                                                                       │
│  ┌──────────────────┐              ┌──────────────────┐            │
│  │   Groq API       │              │   Gemini API     │            │
│  │ (openai/gpt-     │              │ (gemini-2.0-     │            │
│  │  oss-120b)       │              │  flash)          │            │
│  └──────────────────┘              └──────────────────┘            │
└─────────────────────────────────────────────────────────────────────┘
```

## 🔄 Data Flow

### 1. Agent Route Readiness Flow

```
User Input → Frontend → Backend Agent Router → Agent Service
                                                      ↓
                                    ┌─────────────────┴─────────────────┐
                                    │                                   │
                              Tool Execution                    RAG Retrieval
                                    │                                   │
                    ┌───────────────┴───────────┐          ┌────────────┴───────────┐
                    │                           │          │                        │
            get_route_info()          get_delivery_window()  Embed query           │
                    │                           │          │                        │
                    └───────────────┬───────────┘          FAISS search             │
                                    │                      │                        │
                                Context                  Retrieve docs              │
                                    │                      │                        │
                                    └──────────┬───────────┘                        │
                                               │                                    │
                                          LLM Chain                                 │
                                    (Groq → Gemini fallback)                        │
                                               ↓                                    │
                                    AgentRunResult                                  │
                                      (with insights)                               │
                                               ↓                                    │
                                    Save to database                                │
                                               ↓                                    │
                                    Return to frontend
```

### 2. Planner Flow

```
User Input → Frontend → Backend Planner Router → Planner Service
                                                        ↓
                                              Validate parameters
                                                        ↓
                                            Try AI plan generation
                                         (Groq → Gemini fallback)
                                                        ↓
                                            Success? → Return AI plan
                                                 ↓
                                            Fallback → Rule-based template
                                                        ↓
                                              Save to database
                                                        ↓
                                              Return to frontend
```

### 3. Search Tool Flow (Interactive RAG)

```
User Input → Frontend Search Panel → Backend /ai/search endpoint
                                              ↓
                                    Validate query
                                              ↓
                                    Embed query (SentenceTransformers)
                                              ↓
                                    FAISS similarity search
                                              ↓
                                    Retrieve top-k documents
                                              ↓
                                    Format results (content, source, score)
                                              ↓
                                    Return to frontend
                                              ↓
                            Display results in SearchPanel
```

## 🧩 Component Details

### Frontend (React + Vite)

- **Agent Panel**: Route readiness assessment interface
- **Planner Panel**: AI-powered route planning
- **Search Panel**: Interactive knowledge base search
- **History Panel**: View past agent runs and route plans
- **Echo Form**: Test endpoint for retry mechanisms

### Backend (FastAPI)

#### Routers
- `/ai/*` - Agent and search endpoints
- `/planner/*` - Route planning endpoints
- `/gemini/*` - Gemini proxy endpoints
- `/echo` - Test endpoint

#### Services
- **agent_langchain.py**: LangChain-based agent with tool calling
- **planner.py**: AI-powered route planning with validation
- **rag.py**: RAG system with SentenceTransformers + FAISS
- **agent_tools.py**: Tool functions for agent (route info, contacts, etc.)

### Database (PostgreSQL)

#### Tables
- `agent_runs`: Historical agent executions
- `routes`: Route configurations
- `document_chunks`: Embedded knowledge base (30 chunks from 3 documents)

## 🤖 RAG System: Tool vs. Automatic Process

**The RAG system serves BOTH roles:**

### As an Automatic Process
- Runs automatically during agent execution
- Agent retrieves relevant documents based on route context
- Documents are used to enhance LLM prompts
- User doesn't need to explicitly trigger it

### As an Interactive Tool
- Accessible via **Search Panel** in the UI
- Direct endpoint: `GET /ai/search?query=...&k=5`
- Allows users to explore the knowledge base
- Useful for:
  - Finding specific policies
  - Exploring best practices
  - Understanding operational guidelines
  - Independent research outside of agent runs

**Think of it like this:**
- **Automatic RAG** = Google Assistant answering your question using web search automatically
- **Search Tool** = You manually searching Google to explore topics

Both use the same underlying RAG infrastructure (SentenceTransformers + FAISS), but serve different use cases.

## 📚 Knowledge Base

The system contains 30 document chunks from 3 logistics documents:

1. **logistics_knowledge.txt**: Core logistics principles and best practices
2. **fleet_management.txt**: Vehicle maintenance, tracking, and optimization
3. **dispatch_operations.txt**: Dispatch protocols and coordination

Each chunk is:
- Embedded using SentenceTransformers (all-MiniLM-L6-v2)
- Stored as 384-dimensional vectors
- Indexed in FAISS for fast similarity search

## 🔌 External Integrations

### Groq API
- Primary LLM provider
- Model: `openai/gpt-oss-120b`
- Used for: Agent insights, route planning

### Gemini API
- Fallback LLM provider
- Model: `gemini-2.0-flash`
- Used for: Agent insights (if Groq fails), route planning

### LangChain
- Framework for building LLM applications
- Provides: Prompt templates, chains, tool calling
- Integration: `agent_langchain.py`

## 🚀 Deployment

The system runs in Docker Compose with 4 services:

1. **backend** (port 8000): FastAPI application
2. **frontend** (port 5173): React + Vite dev server
3. **db** (port 5432): PostgreSQL database
4. **nginx** (port 8080): Reverse proxy

### Environment Variables

**Backend:**
- `DATABASE_URL`: PostgreSQL connection string
- `GROQ_API_KEY`: Groq API key (optional)
- `GEMINI_API_KEY`: Gemini API key (optional)
- `USE_LANGCHAIN_AGENT`: Enable LangChain agent (default: true)

## 📈 Future Enhancements

- Add more tools to the agent (weather, traffic, etc.)
- Expand knowledge base with more documents
- Implement user authentication
- Add real-time updates via WebSockets
- Deploy to production (AWS/GCP/Azure)
