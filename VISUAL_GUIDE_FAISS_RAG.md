# Visual Guide: FAISS and RAG in the Agent Application

This document provides a visual walkthrough of how FAISS and RAG work in the application, showing what students would see when running the agent.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (React)                          │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │           AgentPanel.jsx Component                         │ │
│  │                                                            │ │
│  │  • Feature Selection Dropdown                             │ │
│  │  • Launch Date Input                                      │ │
│  │  • Audience Role & Experience                             │ │
│  │  • "Run Release Readiness Agent" Button                   │ │
│  │                                                            │ │
│  │  Results Display:                                         │ │
│  │  ├─ Summary                                               │ │
│  │  ├─ Gemini AI Insight (if API key configured)            │ │
│  │  ├─ Recommendations (priority-coded)                      │ │
│  │  ├─ Tool Calls (transparency view)                        │ │
│  │  ├─ RAG Contexts (retrieved documents) ◄── FAISS!        │ │
│  │  └─ Generated Plan                                        │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│                          ▼ HTTP POST                             │
└──────────────────────────│───────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI)                             │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │     /api/ai/release-readiness Endpoint                     │ │
│  │                                                            │ │
│  │  1. Receive AgentRunContext                               │ │
│  │  2. Call run_release_readiness_agent(context, db)         │ │
│  └────────────────────────────────────────────────────────────┘ │
│                           │                                      │
│                           ▼                                      │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │     Agent Service (agent.py)                               │ │
│  │                                                            │ │
│  │  Step 1: Call Tools                                       │ │
│  │    ├─ fetch_feature_brief(slug)                           │ │
│  │    ├─ fetch_launch_window(slug)                           │ │
│  │    ├─ fetch_support_contacts(role)                        │ │
│  │    └─ list_slo_watch_items(slug)                          │ │
│  │                                                            │ │
│  │  Step 2: RAG Retrieval ◄── FAISS HAPPENS HERE            │ │
│  │    ├─ retriever = build_retriever(db)                     │ │
│  │    ├─ search_query = "feature + role + context"           │ │
│  │    └─ rag_contexts = retriever.search(query, k=3)         │ │
│  │                     │                                      │ │
│  │                     ▼                                      │ │
│  │  ┌──────────────────────────────────────────────────────┐ │ │
│  │  │  RAG Service (rag.py) - FAISS Core                   │ │ │
│  │  │                                                       │ │ │
│  │  │  a) Load DocumentChunk rows from PostgreSQL          │ │ │
│  │  │  b) Create FAISS IndexFlatL2(256)                    │ │ │
│  │  │  c) Add all embeddings to index                      │ │ │
│  │  │  d) Embed query: embed_text(query) → vector          │ │ │
│  │  │  e) Search: index.search(query_vec, k=3)             │ │ │
│  │  │  f) Return top 3 chunks with scores                  │ │ │
│  │  └──────────────────────────────────────────────────────┘ │ │
│  │                     │                                      │ │
│  │                     ▼                                      │ │
│  │  Step 3: Generate Gemini Insight (if API key set)        │ │
│  │    ├─ Build prompt with all context                      │ │
│  │    ├─ Include RAG contexts in prompt                     │ │
│  │    └─ Generate strategic insights + recommendations      │ │
│  │                                                            │ │
│  │  Step 4: Build Recommendations                            │ │
│  │    ├─ Deterministic recommendations                       │ │
│  │    └─ Add AI-generated recommendations                    │ │
│  │                                                            │ │
│  │  Step 5: Persist to Database                              │ │
│  │    └─ AgentRun(feature, summary, insights, tool_calls...) │ │
│  │                                                            │ │
│  │  Step 6: Return AgentRunResult                            │ │
│  └────────────────────────────────────────────────────────────┘ │
│                           │                                      │
│                           ▼ JSON Response                        │
└───────────────────────────│──────────────────────────────────────┘
                            │
                            ▼
                 ┌──────────────────────┐
                 │  PostgreSQL Database │
                 │                      │
                 │  ├─ document_chunks  │
                 │  ├─ agent_runs       │
                 │  ├─ plan_runs        │
                 │  └─ resources        │
                 └──────────────────────┘
```

## Example User Flow

### Step 1: User Fills Form

```
┌────────────────────────────────────────┐
│  🤖 Release Readiness Agent           │
│                                        │
│  Feature: [Curriculum Pathways ▼]     │
│  Launch Date: [2025-03-15]            │
│  Audience Role: [Instructor]          │
│  Experience: [Intermediate ▼]         │
│  ☑ Include Risk Analysis              │
│                                        │
│  [ Run Release Readiness Agent ]      │
└────────────────────────────────────────┘
```

### Step 2: Agent Executes (Behind the Scenes)

```
Agent Orchestration Flow:
═══════════════════════════════════════════════════

1. Tool Calls (gather context)
   ✓ fetch_feature_brief("curriculum-pathways")
     → FeatureBrief(name="Curriculum Pathways", summary="...")
   
   ✓ fetch_launch_window("curriculum-pathways")
     → LaunchWindow(window_start=2025-03-01, environment="production")
   
   ✓ fetch_support_contacts("Instructor")
     → [SupportContact(role="Program Manager", ...)]
   
   ✓ list_slo_watch_items("curriculum-pathways")
     → ["API latency exceeds 200ms", ...]

2. RAG Retrieval ← FAISS IN ACTION
   query = "Curriculum Pathways Instructor release launch"
   
   FAISS Process:
   ┌─────────────────────────────────────────┐
   │ embed_text(query)                       │
   │   "Curriculum Pathways..." → [0.2, ...] │
   ├─────────────────────────────────────────┤
   │ FAISS IndexFlatL2.search(vec, k=3)      │
   │   Searches 256-dim space for closest    │
   ├─────────────────────────────────────────┤
   │ Returns top 3 chunks:                   │
   │   • docs/agent.md (score: 0.23)         │
   │   • docs/deployment.md (score: 0.45)    │
   │   • docs/features.md (score: 0.67)      │
   └─────────────────────────────────────────┘

3. Gemini AI Generation (if configured)
   Builds prompt with:
   • Feature details
   • Launch window
   • SLO items
   • RAG contexts ← Grounds the AI response!
   
   → Generates strategic insight and recommendations

4. Assemble Response
   • Summary sentence
   • Gemini insight
   • Recommendations (deterministic + AI)
   • Tool call traces
   • RAG contexts
   • Generated plan

5. Persist to Database
   AgentRun saved to agent_runs table
```

### Step 3: User Sees Results

```
┌──────────────────────────────────────────────────────────────┐
│  📋 Summary                                                   │
│  Curriculum Pathways targets Instructor personas.             │
│  Production window: Mar 01–Mar 15. Success metric:           │
│  80% lesson completion rate.                                  │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│  ✨ AI Insight [Powered by Gemini]                           │
│  Strategic launch assessment: The feature aligns well with    │
│  the academic calendar. Recommend early instructor training   │
│  to maximize adoption. Monitor API performance closely.       │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│  🎯 Recommendations (6)                                       │
│                                                               │
│  1. [HIGH] Confirm launch communications                     │
│     Share the feature brief with Sarah Chen and align on     │
│     messaging for the production window.                     │
│                                                               │
│  2. [HIGH] Validate operational readiness                    │
│     Ensure runbooks and dashboards reflect the new flow.     │
│                                                               │
│  3. [HIGH] Mitigate top risk                                 │
│     Create a mitigation plan for: API latency exceeds 200ms. │
│                                                               │
│  4. [MEDIUM] Broadcast stakeholder update                    │
│     Send tailored update to secondary contacts.              │
│                                                               │
│  5. [MEDIUM] [AI] Review documentation coverage              │
│     Gemini recommends expanding setup guides for new users.  │
│                                                               │
│  6. [LOW] [AI] Schedule post-launch retrospective            │
│     Plan review session within 2 weeks of launch.            │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│  🔧 Tool Calls                                                │
│                                                               │
│  • fetch_feature_brief(feature_slug="curriculum-pathways")   │
│    → Curriculum Pathways: Student learning path builder      │
│                                                               │
│  • fetch_launch_window(feature_slug="curriculum-pathways")   │
│    → production window 2025-03-01 → 2025-03-15               │
│                                                               │
│  • fetch_support_contacts(audience_role="Instructor")        │
│    → 2 contact(s) notified                                   │
│                                                               │
│  • list_slo_watch_items(feature_slug="curriculum-pathways")  │
│    → API latency exceeds 200ms, Database connection pool...  │
│                                                               │
│  • rag_retrieval(query="Curriculum...", k=3)                 │
│    → Retrieved 3 relevant document(s)   ◄── FAISS RESULT!   │
│                                                               │
│  • gemini_insight_generation(model="gemini-2.0-flash")       │
│    → Strategic launch assessment: The feature aligns...      │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│  📚 Retrieved Context (RAG)   ◄── FAISS OUTPUT DISPLAYED     │
│                                                               │
│  1. docs/agent                                                │
│     "The release readiness agent orchestrates multiple tools  │
│     to assess launch preparedness. It integrates with FAISS  │
│     for document retrieval and Gemini for AI insights."      │
│     Score: 0.2314                                             │
│                                                               │
│  2. docs/deployment                                           │
│     "Deploy the application using docker compose up --build  │
│     in the ai-web directory. The agent will be available at  │
│     localhost:8080 behind the Nginx reverse proxy."          │
│     Score: 0.4521                                             │
│                                                               │
│  3. docs/features                                             │
│     "Feature briefs provide structured information about      │
│     upcoming releases including target audience, success     │
│     metrics, and launch windows."                            │
│     Score: 0.6789                                             │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│  📝 Generated Plan (6 steps)                                  │
│                                                               │
│  1. Notify stakeholders                                       │
│     Alert Instructor about Curriculum Pathways launch...     │
│                                                               │
│  2. Prepare documentation                                     │
│     Gather setup guides and FAQs for Instructor...           │
│                                                               │
│  3. Review risk mitigation                                    │
│     Evaluate contingency plans for API latency...            │
│                                                               │
│  ...and 3 more steps                                          │
└──────────────────────────────────────────────────────────────┘
```

## Key Learning Points

### 1. FAISS Makes RAG Possible

Without FAISS:
- Manual keyword search (slow, inaccurate)
- No semantic understanding
- Can't scale to many documents

With FAISS:
- ✓ Semantic similarity search
- ✓ Millisecond searches
- ✓ Scales to millions of documents
- ✓ Shows which docs were relevant

### 2. RAG Grounds AI Responses

**Without RAG:**
```
User: "What are the launch risks?"
AI: "Common risks include downtime, bugs, and user confusion."
     ↑ Generic, might not apply
```

**With RAG:**
```
User: "What are the launch risks?"
System: [FAISS retrieves actual SLO watch items]
AI: "Based on the feature data, key risks are:
     1. API latency exceeds 200ms (monitor closely)
     2. Database connection pool exhaustion (add replicas)"
     ↑ Specific, grounded in actual data
```

### 3. Transparency via Tool Calls

Students can see:
- **What** the agent did (which tools)
- **When** RAG retrieval happened
- **What** was retrieved (actual chunks)
- **How** AI used the context (in insights)

This is critical for:
- Debugging agent behavior
- Understanding decision-making
- Building trust in AI systems
- Auditing for compliance

### 4. Complete Integration

The system shows a production-grade stack:
- ✓ **Frontend**: React + hooks for state management
- ✓ **Backend**: FastAPI + service layer pattern
- ✓ **Database**: PostgreSQL with Alembic migrations
- ✓ **Vector Search**: FAISS for semantic retrieval
- ✓ **AI**: Gemini for intelligent insights
- ✓ **Orchestration**: Agent pattern with tool abstractions
- ✓ **Persistence**: All runs saved for auditing

## Testing the Application

Students should test:

### 1. Without GEMINI_API_KEY
```bash
# In backend/.env
GEMINI_API_KEY=

# Start the stack
cd ai-web
docker compose up --build

# Test
curl http://localhost:8000/api/ai/release-readiness \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "feature_slug": "curriculum-pathways",
    "launch_date": "2025-03-15",
    "audience_role": "Instructor",
    "audience_experience": "intermediate",
    "include_risks": true
  }'
```

**Expected Result:**
- ✓ Summary generated
- ✗ No gemini_insight (null)
- ✓ Deterministic recommendations
- ✓ Tool calls tracked
- ✓ RAG contexts retrieved ← FAISS works!
- ✓ used_gemini: false

### 2. With GEMINI_API_KEY
```bash
# In backend/.env
GEMINI_API_KEY=your-actual-key-here

# Restart backend
docker compose restart backend

# Test same endpoint
```

**Expected Result:**
- ✓ Summary generated
- ✓ gemini_insight populated with AI text
- ✓ Deterministic + AI recommendations
- ✓ Tool calls include gemini_insight_generation
- ✓ RAG contexts retrieved ← FAISS works!
- ✓ used_gemini: true

### 3. Check Frontend
```bash
# Open browser
http://localhost:8080

# Navigate to Agent Panel
# Fill form and click "Run Release Readiness Agent"
# Observe:
# - Results display with all sections
# - RAG contexts show retrieved documents
# - Tool calls are transparent
# - History updates with new run
```

## Comparison: Custom vs LangChain

### Our Implementation (Custom)
```python
# rag.py
def embed_text(text: str) -> np.ndarray:
    vector = np.zeros(256, dtype="float32")
    for token in _tokenize(text):
        vector[hash(token) % 256] += 1.0
    # normalize...
    return vector

retriever = build_retriever(db)
contexts = retriever.search(query, k=3)
```

**Pros:**
- ✓ Full control
- ✓ No external dependencies
- ✓ Works offline
- ✓ Educational value

**Cons:**
- ✗ Simple hashing (not semantic)
- ✗ Manual index management
- ✗ No advanced features

### LangChain Implementation
```python
from langchain.vectorstores import FAISS
from langchain.embeddings import GoogleGenerativeAIEmbeddings

embeddings = GoogleGenerativeAIEmbeddings(model="text-embedding-004")
vectorstore = FAISS.from_documents(chunks, embeddings)
contexts = vectorstore.similarity_search(query, k=3)
```

**Pros:**
- ✓ Production-quality embeddings
- ✓ Standardized interface
- ✓ Easy to switch providers
- ✓ Advanced features (MMR, etc.)

**Cons:**
- ✗ API dependency
- ✗ Less educational
- ✗ More abstraction layers

## Summary

The enhanced Lab05_6_7_8 notebook now provides:

1. **Complete FAISS explanation**: What it is, how it works, why we use it
2. **RAG workflow visualization**: Step-by-step process with diagrams
3. **Code walkthrough**: Line-by-line explanation of rag.py
4. **Integration details**: How agent.py uses RAG
5. **LangChain comparison**: Future path for production systems
6. **LangSmith introduction**: Observability and monitoring tools
7. **Practical examples**: What students will see when running the app

Students leave with:
- ✓ Understanding of embeddings and vector search
- ✓ Knowledge of FAISS index types and usage
- ✓ RAG architecture comprehension
- ✓ Production-ready code examples
- ✓ Path to adopting industry tools (LangChain/LangSmith)
- ✓ Ability to build and debug AI agents
