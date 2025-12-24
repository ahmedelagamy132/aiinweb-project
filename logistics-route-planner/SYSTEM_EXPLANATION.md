# Logistics Route Planner System - Technical Overview

## What This System Does

This is a **Logistics Route Planning Assistant** that helps teams prepare for delivery route launches. It combines:

1. **Route Planning Service** - Generates structured delivery route plans with steps, timelines, and acceptance criteria
2. **AI Agent Service** - An intelligent agent that provides route readiness assessments using multiple data sources
3. **RAG (Retrieval-Augmented Generation)** - Searches through logistics documentation to provide relevant context
4. **LLM Integration** - Uses Gemini or Groq LLMs to generate insights and recommendations

---

## System Architecture

### Frontend (React + Vite)
- User interface for interacting with the planner and agent
- Features include:
  - **Planner Panel**: Generate route plans based on goals and audience
  - **Agent Panel**: Get AI-powered route readiness assessments
  - **Echo Form**: Test API connectivity

### Backend (FastAPI + Python)
- RESTful API with multiple routers:
  - `/api/planner/*` - Route plan generation
  - `/api/ai/*` - AI agent operations
  - `/api/echo` - Connection testing
  - `/api/gemini` - Direct Gemini API testing

### Database (PostgreSQL)
- Stores:
  - Route run history
  - Agent execution history
  - Document chunks with embeddings for RAG
  - Echo attempt tracking

---

## Where LLMs Generate Content

### 1. **AI Agent Service** (`backend/app/services/agent.py`)
**Purpose**: Generate intelligent insights and recommendations for route launches

**LLM Usage**:
- **Input**: Gathers context from multiple sources:
  - Route brief (name, summary, target audience, success metrics)
  - Delivery window (dates, environment, freeze requirements)
  - SLO watch items (risks to monitor)
  - RAG retrieved documentation (relevant logistics knowledge)
  - User preferences (launch date, risk analysis preference)

- **LLM Processing**: 
  - Calls either **Groq** (preferred) or **Gemini** LLM
  - Uses prompt engineering to request:
    1. Strategic insight (2-3 sentences)
    2. Two specific AI-generated recommendations with priorities
  
- **Output**: Returns structured recommendations like:
  ```
  INSIGHT: The express delivery route requires careful driver briefing...
  RECOMMENDATION_1: Pre-stage emergency contacts|Ensure backup drivers...|high
  RECOMMENDATION_2: Monitor traffic patterns|Set up real-time alerts...|medium
  ```

**Files**:
- `_generate_groq_insight()` - Uses Groq API with streaming
- `_generate_gemini_insight()` - Uses Google Gemini API
- Both functions parse LLM responses and structure them as `AgentRecommendation` objects

### 2. **Route Planner Service** (`backend/app/services/planner.py`)
**Purpose**: Generate structured route plans

**LLM Usage**: **NONE** - This is purely rule-based/deterministic
- Uses if/else logic based on audience experience level
- No AI/LLM involved - just template-based generation
- Builds `RouteStep` objects with predefined criteria

---

## RAG (Retrieval-Augmented Generation) System

### How It Works

**Purpose**: Provide relevant logistics knowledge to the LLM for better recommendations

**Components**:

1. **Document Storage** (`backend/app/models.py` - `DocumentChunk`)
   - Documents are split into ~500-character chunks with overlap
   - Each chunk has: content, source file, unique slug, embedding vector

2. **Embedding Generation** (`backend/app/services/rag.py`)
   - **NEW**: Uses **SentenceTransformers** (all-MiniLM-L6-v2 model)
   - Converts text → 384-dimensional dense vectors
   - Semantic embeddings capture meaning, not just keywords
   - **REPLACED**: Old system used simple hash-based bag-of-words (256-dim)

3. **Vector Search** (FAISS)
   - Builds FAISS index from all document embeddings
   - Given a query, finds k-nearest chunks by cosine similarity
   - Returns top matching documents with similarity scores

4. **Retrieval Flow**:
   ```
   User Query → Embed Query → FAISS Search → Retrieve Top K Chunks → Feed to LLM
   ```

### Documents Ingested

Three domain-specific documents covering:

1. **logistics_knowledge.txt**
   - Route optimization fundamentals
   - Delivery time windows and vehicle capacity
   - Driver safety and HOS compliance
   - Last-mile challenges, cross-country freight
   - Performance metrics and KPIs
   - Communication protocols and risk mitigation
   - Technology integration and environmental considerations

2. **fleet_management.txt**
   - Vehicle maintenance scheduling
   - Driver assignment optimization
   - Fuel management and GPS tracking
   - Compliance and regulatory requirements
   - Cargo securement standards
   - Training, emergency procedures
   - Fleet replacement strategies and telematics

3. **dispatch_operations.txt**
   - Dispatch center operations
   - Order management workflow
   - Dynamic route adjustment
   - Customer communication standards
   - Load planning and staging
   - Driver check-in/out procedures
   - Exception handling and performance monitoring
   - Shift planning and peak season preparation

**Total**: 30 chunks ingested with semantic embeddings

---

## Complete Workflow Example

### When a User Requests Route Readiness Assessment:

1. **Frontend** (`useAgent.js`): User selects route, sets preferences, clicks "Run Agent"

2. **API Call** → `POST /api/ai/route-readiness`

3. **Agent Service** (`agent.py` - `run_route_readiness_agent()`):
   
   a. **Tool Calls** (Deterministic - NO LLM):
      - `fetch_route_brief()` - Get route details
      - `fetch_delivery_window()` - Get timeline
      - `fetch_support_contacts()` - Get stakeholder contacts
      - `list_slo_watch_items()` - Get risk items

   b. **RAG Retrieval** (NO LLM):
      - Build query: "Express Delivery Route Driver delivery logistics"
      - Embed query using SentenceTransformers
      - FAISS search returns top 3 relevant chunks
      - Example: chunks about driver safety, urban delivery, time windows

   c. **LLM Insight Generation** (LLM USED HERE):
      - Construct prompt with all gathered context
      - Call Groq or Gemini LLM
      - Parse response into structured recommendations

   d. **Plan Generation** (NO LLM):
      - Call `build_route_plan()` - rule-based template

   e. **Response Assembly**:
      - Combine LLM insights + deterministic recommendations
      - Return structured JSON to frontend

4. **Database Persistence**:
   - Save `AgentRun` record for auditing
   - Tracks which LLM was used, what was retrieved, what was recommended

5. **Frontend Display**:
   - Show summary, insights, recommendations, plan steps
   - Display RAG sources that were used
   - Show tool call trace for transparency

---

## Key Technical Details

### SentenceTransformers Integration

**Model**: `all-MiniLM-L6-v2`
- Lightweight (90MB) but effective
- 384-dimensional embeddings
- Pre-trained on semantic similarity tasks
- Fast inference (~20ms per text on CPU)

**Advantages over old hash-based approach**:
- ✓ Understands semantic meaning ("vehicle" ≈ "truck" ≈ "fleet")
- ✓ Captures context and relationships
- ✓ Better retrieval quality for RAG
- ✗ Requires model download (~90MB first time)
- ✗ Slightly slower than hash (but still fast)

### LLM Providers

**Groq** (Preferred):
- Fast inference on custom hardware
- Model: `openai/gpt-oss-120b` (configurable via GROQ_MODEL env var)
- Streaming responses
- Requires: `GROQ_API_KEY` in environment

**Gemini** (Fallback):
- Google's generative AI
- Model: `gemini-2.0-flash` (configurable via GEMINI_MODEL env var)
- Requires: `GEMINI_API_KEY` in environment

**If neither available**: System still works but returns only deterministic recommendations

### Database Schema

**DocumentChunk Table**:
```
id: int (primary key)
slug: string (unique identifier like "logistics_knowledge_chunk_0")
source: string (filename like "logistics_knowledge.txt")
content: text (chunk text)
embedding: JSONB (list of 384 floats)
created_at: timestamp
```

**AgentRun Table**:
```
id: int (primary key)
route_slug: string (which route was analyzed)
audience_role: string (Driver, Fleet Manager, etc.)
audience_experience: string (beginner/intermediate/advanced)
summary: text (generated summary)
gemini_insight: text (LLM-generated insight, nullable)
recommended_actions: JSONB (list of recommendations)
tool_calls: JSONB (trace of what the agent did)
rag_contexts: JSONB (which documents were retrieved)
used_gemini: boolean (true if LLM was used)
created_at: timestamp
```

---

## Running the System

### Start Services:
```bash
docker-compose up -d
```

### Ingest Documents (one-time):
```bash
docker-compose exec backend python ingest_documents.py
```

### Access:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Nginx Proxy: http://localhost:8080

---

## Summary

**What uses LLM**:
- ✓ AI Agent insight generation (`_generate_groq_insight`, `_generate_gemini_insight`)
- ✓ Recommendation generation (2 AI recommendations added to deterministic ones)

**What doesn't use LLM**:
- ✗ Route plan generation (template-based)
- ✗ Tool calls (fetch route briefs, contacts, etc.)
- ✗ RAG retrieval (semantic search via embeddings)
- ✗ Document chunking and ingestion
- ✗ Database operations

**RAG Flow**:
Documents → Chunk → Embed (SentenceTransformers) → Store → Query Embed → FAISS Search → Retrieve → Context for LLM

**End-to-End**:
User Input → Agent gathers context → RAG finds relevant docs → LLM generates insights → Combine with rules → Return structured response
