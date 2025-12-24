# Quick System Overview - Logistics Route Planner

## 🎯 What Is This System?

An AI-powered logistics route planning system that helps assess route readiness and generate optimized delivery plans using:
- **RAG (Retrieval-Augmented Generation)** for knowledge-based recommendations
- **LangChain** for structured AI agent workflows
- **Groq/Gemini LLMs** for intelligent insights
- **React Frontend** for user interaction

## 📐 Simple Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      🖥️  USER                                │
│                  (Web Browser)                               │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│              ⚛️  REACT FRONTEND (Port 5173)                  │
│  • Agent Panel: Route readiness check                       │
│  • Planner Panel: Generate route plans                      │
│  • Search Panel: Query knowledge base                       │
│  • History Panel: View past runs                            │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP /api/*
                       ↓
┌─────────────────────────────────────────────────────────────┐
│              🌐  NGINX PROXY (Port 8080)                     │
│  Routes /api/* → Backend                                    │
│  Routes /* → Frontend                                       │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│          🚀  FASTAPI BACKEND (Port 8000)                     │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 🤖  AI AGENT                                         │  │
│  │  Step 1: Gather route context (tools)               │  │
│  │  Step 2: Search knowledge base (RAG) ←─────┐        │  │
│  │  Step 3: Analyze with LLM (Groq/Gemini)    │        │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                     │        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 📋  PLANNER                                          │  │
│  │  Generate AI route plans with validation            │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                     │        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 🔍  RAG SYSTEM                              ←────────┘  │
│  │  • SentenceTransformers embeddings (384-dim)        │  │
│  │  • FAISS vector search                               │  │
│  │  • 30 logistics document chunks                      │  │
│  │                                                       │  │
│  │  Two Modes:                                          │  │
│  │  1. Automatic (during agent runs)                   │  │
│  │  2. Interactive (via search endpoint)               │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│            🗄️  POSTGRESQL DATABASE                          │
│  • agent_runs: Agent execution history                      │
│  • routes: Route configurations                             │
│  • document_chunks: Embedded knowledge (30 chunks)          │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│              ☁️  EXTERNAL AI APIs                            │
│  • Groq (openai/gpt-oss-120b)                               │
│  • Gemini (gemini-2.0-flash)                                │
└─────────────────────────────────────────────────────────────┘
```

## 🔄 How Data Flows

### Agent Workflow (Route Readiness)
```
1. User selects route → Frontend sends request
2. Backend agent gathers context using tools
3. Agent queries RAG system for relevant docs
4. RAG embeds query and searches FAISS
5. Agent sends context + docs to LLM
6. LLM generates insights and recommendations
7. Save results to database
8. Return to frontend for display
```

### Planner Workflow (Route Planning)
```
1. User enters route details → Frontend sends request
2. Backend validates parameters
3. Try AI plan generation (Groq → Gemini fallback)
4. If AI fails, use rule-based template
5. Save plan to database
6. Return to frontend
```

### Search Workflow (Interactive RAG)
```
1. User types query → Frontend sends request
2. Backend embeds query with SentenceTransformers
3. FAISS finds top-k similar documents
4. Return results with scores
5. Display in search panel
```

## 💡 RAG: Tool or Automatic?

**BOTH!**

### Automatic Mode 🔄
- Runs automatically when agent assesses routes
- Agent doesn't need to explicitly call it
- Transparent to the user
- Example: "Check route NYC-BOS" → Agent automatically searches for NYC/BOS docs

### Interactive Tool Mode 🔍
- Available via Search Panel in UI
- User explicitly queries knowledge base
- Direct exploration of logistics docs
- Example: User searches "vehicle maintenance schedule"

**Analogy:** 
- **Automatic** = Autocorrect fixing typos as you type
- **Tool** = Manually opening spell checker to review a word

## 🎨 UI Structure

```
┌─────────────┬──────────────────────────────────────────────┐
│             │  Main Content Area                           │
│  Sidebar    │                                              │
│             │  ┌────────────────────────────────────────┐  │
│  🤖 Agent   │  │                                        │  │
│  📋 Planner │  │      Active Tab Content                │  │
│  🔍 Search  │  │      (Cards with forms/results)        │  │
│  📜 History │  │                                        │  │
│  📦 Echo    │  │                                        │  │
│             │  └────────────────────────────────────────┘  │
└─────────────┴──────────────────────────────────────────────┘
```

## 📊 Tech Stack Summary

| Layer | Technology |
|-------|-----------|
| Frontend | React 18 + Vite |
| Backend | FastAPI + Python 3.11 |
| Database | PostgreSQL 16 |
| AI Framework | LangChain |
| LLMs | Groq + Gemini (fallback) |
| Embeddings | SentenceTransformers (all-MiniLM-L6-v2) |
| Vector DB | FAISS |
| Deployment | Docker Compose |

## 🚀 Quick Start

```bash
# Start all services
docker-compose up -d

# Ingest knowledge base
docker-compose exec backend python ingest_documents.py

# Access UI
open http://localhost:8080
```

## 📚 Knowledge Base

3 logistics documents with 30 total chunks:
1. **logistics_knowledge.txt** - Core principles
2. **fleet_management.txt** - Vehicle operations
3. **dispatch_operations.txt** - Dispatch protocols

Each chunk is:
- Split with sentence overlap
- Embedded to 384-dimensional vector
- Indexed in FAISS for fast search
- Retrieved based on semantic similarity

## 🔑 Key Features

✅ **AI-Powered Route Planning** - LLM generates optimized plans  
✅ **Route Readiness Assessment** - Agent evaluates readiness with AI insights  
✅ **Interactive Document Search** - Query logistics knowledge base  
✅ **Historical Tracking** - View past agent runs and plans  
✅ **Automatic RAG** - AI automatically retrieves relevant docs  
✅ **LangChain Integration** - Structured agent workflows  
✅ **Fallback Systems** - Groq → Gemini → Rule-based  

## 🎯 Use Cases

1. **Dispatcher Planning**: Generate optimized route plans
2. **Route Validation**: Check if route is ready for execution
3. **Knowledge Search**: Find policies and best practices
4. **Historical Analysis**: Review past decisions and outcomes
