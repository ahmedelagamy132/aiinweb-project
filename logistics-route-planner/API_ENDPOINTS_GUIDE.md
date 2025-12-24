# API Endpoints Guide

## Access URLs

The application can be accessed through two methods:

### Method 1: Vite Dev Server (Development)
- **URL**: `http://localhost:5173`
- **How it works**: Vite dev server with built-in proxy to backend
- **Proxy config**: `/api/*` → `http://backend:8000/*` (strips `/api` prefix)
- **Advantages**: Hot module replacement, fast refresh, dev tools

### Method 2: Nginx (Production-like)
- **URL**: `http://localhost:8080`
- **How it works**: Nginx reverse proxy
- **Proxy config**: 
  - `/api/*` → `http://backend:8000/*` (strips `/api` prefix)
  - `/*` → `http://frontend:5173/*` (serves frontend)
- **Advantages**: Production-like environment, single port access

## Available API Endpoints

All API endpoints are prefixed with `/api/ai` when accessed through the frontend.

### 1. List Available Routes
- **Endpoint**: `GET /api/ai/routes`
- **Description**: Retrieves all available delivery routes
- **Response**:
```json
{
  "routes": [
    {
      "slug": "express-delivery",
      "name": "Express Delivery Route",
      "summary": "...",
      "audience_role": "Driver",
      "has_delivery_window": true,
      "delivery_date": "2025-01-15"
    }
  ],
  "total": 3
}
```

### 2. Get Agent History
- **Endpoint**: `GET /api/ai/history?limit=5`
- **Description**: Retrieves recent agent assessment runs
- **Query Params**: `limit` (optional, default: 10)
- **Response**:
```json
{
  "runs": [
    {
      "id": 24,
      "route_slug": "express-delivery",
      "audience_role": "Driver",
      "summary": "...",
      "gemini_insight": "...",
      "used_gemini": true,
      "created_at": "2025-12-24T15:59:57.167557"
    }
  ],
  "total": 5
}
```

### 3. Route Readiness Assessment
- **Endpoint**: `POST /api/ai/route-readiness`
- **Description**: Performs AI-powered route readiness assessment
- **Request Body**:
```json
{
  "route_slug": "express-delivery",
  "audience_role": "Driver",
  "use_gemini_insights": true
}
```
- **Response**:
```json
{
  "summary": "...",
  "route_name": "Express Delivery Route",
  "delivery_window": "...",
  "tool_calls": [
    {
      "tool": "fetch_route_brief",
      "arguments": {"route_slug": "express-delivery"},
      "output_preview": "..."
    }
  ],
  "gemini_insight": "...",
  "run_id": 24
}
```

### 4. RAG Search
- **Endpoint**: `POST /api/ai/search`
- **Description**: Semantic search over logistics knowledge base
- **Request Body**:
```json
{
  "query": "driver safety procedures"
}
```

## Backend Router Structure

The FastAPI backend defines routes with the `/ai` prefix:

```python
# backend/app/routers/agent.py
router = APIRouter(prefix="/ai", tags=["ai"])

@router.get("/routes")        # → /ai/routes
@router.get("/history")       # → /ai/history
@router.post("/route-readiness")  # → /ai/route-readiness
@router.post("/search")       # → /ai/search
```

## Proxy Flow

### Request Flow (Vite Dev Server)
```
Browser → http://localhost:5173/api/ai/routes
  ↓
Vite proxy: Strips /api prefix
  ↓
http://backend:8000/ai/routes
  ↓
FastAPI router handles /ai/routes
  ↓
Response ← 200 OK with JSON data
```

### Request Flow (Nginx)
```
Browser → http://localhost:8080/api/ai/routes
  ↓
Nginx: proxy_pass http://backend:8000/ (strips /api)
  ↓
http://backend:8000/ai/routes
  ↓
FastAPI router handles /ai/routes
  ↓
Response ← 200 OK with JSON data
```

## Testing Endpoints

### Test through Vite (port 5173):
```bash
curl http://localhost:5173/api/ai/routes | jq '.total'
curl 'http://localhost:5173/api/ai/history?limit=5' | jq '.total'
```

### Test through Nginx (port 8080):
```bash
curl http://localhost:8080/api/ai/routes | jq '.total'
curl 'http://localhost:8080/api/ai/history?limit=5' | jq '.total'
```

### Test backend directly (port 8000):
```bash
curl http://localhost:8000/ai/routes | jq '.total'
curl 'http://localhost:8000/ai/history?limit=5' | jq '.total'
```

## Troubleshooting

### Issue: 404 Not Found
- **Cause**: Wrong URL path or missing proxy configuration
- **Solution**: Ensure using `/api/ai/*` pattern, not `/ai/*` when accessing through frontend

### Issue: Connection Refused
- **Cause**: Wrong port or container not running
- **Solution**: 
  - Check `docker-compose ps` to verify all containers are running
  - Use port 5173 (Vite) or 8080 (Nginx), not 80

### Issue: 500 Internal Server Error
- **Cause**: Backend code error or missing dependencies
- **Solution**: Check backend logs with `docker-compose logs backend --tail=50`

### Issue: Cached Errors in Browser
- **Cause**: Browser cached previous failed responses
- **Solution**: Hard refresh with `Ctrl+Shift+R` or clear browser cache

## Configuration Files

### Vite Proxy: `frontend/vite.config.js`
```javascript
proxy: {
  '/api': {
    target: 'http://backend:8000',
    changeOrigin: true,
    rewrite: (path) => path.replace(/^\/api/, ''),
  },
}
```

### Nginx Proxy: `nginx/default.conf`
```nginx
location /api/ {
  proxy_pass http://backend:8000/;
  proxy_set_header Host $host;
  proxy_set_header X-Real-IP $remote_addr;
}
```

### Docker Ports: `docker-compose.yml`
```yaml
services:
  backend:
    ports:
      - "8000:8000"
  frontend:
    ports:
      - "5173:5173"
  nginx:
    ports:
      - "8080:80"
```
