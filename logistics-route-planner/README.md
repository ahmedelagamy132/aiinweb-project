# Logistics Route Planner Launch Assistant

An AI-powered logistics route planning application built with **FastAPI** and **React**. This project demonstrates a production-grade architecture with:

- **Gemini AI Integration** for intelligent route recommendations
- **FAISS-based RAG** for retrieving relevant documentation
- **PostgreSQL Persistence** for auditing and history
- **Docker Compose** orchestration for easy deployment

## 🚀 Features

### Backend (FastAPI)
- **Health/Echo Routes**: Service status checks and retry demonstration
- **Gemini Proxy**: AI-powered content generation endpoint
- **Planner Validation**: Structured route plan generation and validation
- **Release-Readiness Agent**: Full agent workflow with RAG + Gemini + persistence
- **History & Listing APIs**: Audit trail and route metadata

### Frontend (React + Vite)
- **Agent Dashboard**: Run readiness assessments with AI insights
- **Echo Form with Retry**: Demonstrates retry patterns for transient failures
- **Route Planner**: Generate structured delivery plans
- **Modern UI**: Dark theme with glassmorphism and smooth animations

## 📁 Project Structure

```
logistics-route-planner/
├── docker-compose.yml       # Container orchestration
├── README.md                # This file
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── alembic/             # Database migrations
│   │   └── versions/
│   └── app/
│       ├── main.py          # FastAPI entry point
│       ├── config.py        # Settings management
│       ├── database.py      # SQLAlchemy session
│       ├── models.py        # Database models
│       ├── routers/         # API endpoints
│       ├── schemas/         # Pydantic models
│       └── services/        # Business logic
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   └── src/
│       ├── App.jsx          # Main component
│       ├── App.css          # Styling
│       ├── lib/             # API utilities
│       └── features/        # Feature modules
└── nginx/
    └── default.conf         # Reverse proxy config
```

## 🛠️ Setup & Installation

### Prerequisites
- Docker and Docker Compose
- (Optional) Node.js 20+ for local frontend development
- (Optional) Python 3.11+ for local backend development

### Quick Start with Docker

1. **Clone and navigate to the project:**
   ```bash
   cd logistics-route-planner
   ```

2. **Create environment file:**
   ```bash
   # Copy the template and add your Gemini API key
   cp backend/env-template.txt backend/.env
   # Edit backend/.env and add your GEMINI_API_KEY
   ```

3. **Start all services:**
   ```bash
   docker compose up --build
   ```

4. **Access the application:**
   - Frontend: http://localhost:8080 (via Nginx)
   - Backend API: http://localhost:8000
   - Direct Frontend: http://localhost:5173

### Local Development

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## 🔧 Environment Variables

### Backend (.env)
| Variable | Description | Default |
|----------|-------------|---------|
| `GEMINI_API_KEY` | Google Gemini API key | (required for AI features) |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+psycopg2://logistics:logistics@db:5432/logistics` |
| `CORS_ORIGINS` | Allowed origins for CORS | `http://localhost:5173,http://localhost:8080` |

### Frontend
| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_BASE` | Backend API base URL | `http://localhost:8000` |

## 📡 API Endpoints

### Health & Echo
- `GET /health` - Service health check
- `POST /echo` - Flaky echo with retry simulation

### Gemini
- `POST /gemini/generate` - Generate content with Gemini AI
- `GET /gemini/status` - Check Gemini configuration status

### Route Planner
- `POST /planner/route` - Generate a structured route plan
- `POST /planner/route/validate` - Validate/repair plan JSON
- `GET /planner/route/history` - List recent plans

### Route Readiness Agent
- `POST /ai/route-readiness` - Run the full agent pipeline
- `GET /ai/history` - Retrieve agent run history
- `GET /ai/routes` - List available routes

## 🧪 Testing

Verify the application with curl:

```bash
# Health check
curl http://localhost:8000/health

# List available routes
curl http://localhost:8000/ai/routes

# Run agent (replace with actual route slug)
curl -X POST http://localhost:8000/ai/route-readiness \
  -H "Content-Type: application/json" \
  -d '{
    "route_slug": "express-delivery",
    "launch_date": "2025-01-15",
    "audience_role": "Driver",
    "audience_experience": "intermediate",
    "include_risks": true
  }'
```

## 🏗️ Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Nginx     │────▶│  Frontend   │     │  PostgreSQL │
│   :8080     │     │  (Vite)     │     │   (DB)      │
└─────────────┘     │  :5173      │     └─────────────┘
      │             └─────────────┘            ▲
      │                    │                   │
      ▼                    ▼                   │
┌─────────────────────────────────────┐        │
│           Backend (FastAPI)          │────────┘
│              :8000                   │
│  ┌─────────┐ ┌─────────┐ ┌────────┐ │
│  │ Routers │ │Services │ │  RAG   │ │
│  └─────────┘ └─────────┘ └────────┘ │
└─────────────────────────────────────┘
```

## 📚 Sample Routes

The application comes with three pre-configured routes:

1. **Express Delivery Route** - Same-day urban deliveries
2. **Cross-Country Freight Route** - Long-haul optimization
3. **Last Mile Delivery Route** - Residential area delivery

## 🔒 Security Notes

- Never commit `.env` files with real API keys
- The Gemini API key is optional - the app works without AI features
- CORS is configured for local development; adjust for production

## 📄 License

This project is for educational purposes as part of the AI in Web Programming course.
