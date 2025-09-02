# IPTV Playlist Manager - Frontend Connectivity Fix

## Architecture Clarification

The IPTV Playlist Manager is designed as a **unified single-container application** that serves both the React frontend and FastAPI backend from **port 8000 only**.

### ✅ Correct Architecture
- **Port 8000**: Serves both React frontend (at `/`) and API (at `/api/*`)
- **Single Process**: One uvicorn server handles all requests
- **Static Files**: React build is served by FastAPI StaticFiles
- **SPA Routing**: All non-API routes fallback to React app for client-side routing

### ❌ Common Misconception
Users often expect separate ports:
- Port 8000 for backend API ❌
- Port 3000 for frontend ❌

**This is incorrect for our container architecture.**

## Fixed Docker Compose Configuration

### ✅ Correct Configuration
```yaml
services:
  iptv-playlist-manager:
    image: ghcr.io/dander11/iptv-playlist-manager:latest
    container_name: iptv-playlist-manager
    restart: unless-stopped
    ports:
      - "8000:8000"  # Single port for both frontend and API
    environment:
      - CORS_ORIGINS=http://localhost:8000  # Same port
      - JWT_SECRET=your-secret-key-here
      - DATABASE_URL=sqlite:///app/data/app.db
    volumes:
      - ./data:/app/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### ❌ Incorrect Configuration (from defect report)
```yaml
# DON'T USE THIS - IT WON'T WORK
ports:
  - "8001:8000"  # Backend API
  - "8002:3000"  # Frontend (this port doesn't exist in container)
environment:
  - CORS_ORIGINS=http://localhost:8002  # Wrong port
  - REACT_APP_API_URL=http://localhost:8001  # Wrong port
```

## Service Access Points

### Frontend Web Interface
- **URL**: `http://localhost:8000`
- **What it serves**: Complete React application
- **Features**: Full web UI for playlist management

### API Access
- **API Root**: `http://localhost:8000/api`
- **Documentation**: `http://localhost:8000/docs`
- **Health Check**: `http://localhost:8000/health`
- **System Info**: `http://localhost:8000/api/info`

### Direct API Endpoints
- **Authentication**: `http://localhost:8000/api/auth/*`
- **Playlists**: `http://localhost:8000/api/playlists/*`
- **Channels**: `http://localhost:8000/api/channels/*`
- **Validation**: `http://localhost:8000/api/validation/*`
- **System**: `http://localhost:8000/api/system/*`

## Testing the Fixed Configuration

### 1. Test Frontend Access
```bash
curl http://localhost:8000/
# Should return HTML content (React app)
```

### 2. Test API Access
```bash
curl http://localhost:8000/api
# Should return JSON with API information and available endpoints
```

### 3. Test API Documentation
```bash
# Open in browser
http://localhost:8000/docs
```

### 4. Test Health Check
```bash
curl http://localhost:8000/health
# Should return: {"status":"healthy","service":"IPTV Playlist Manager"}
```

## Migration Guide for Existing Users

### If You're Using the Incorrect Configuration

**Old (broken):**
```yaml
ports:
  - "8001:8000"
  - "8002:3000"
environment:
  - CORS_ORIGINS=http://localhost:8002
  - REACT_APP_API_URL=http://localhost:8001
```

**New (working):**
```yaml
ports:
  - "8000:8000"  # Single port
environment:
  - CORS_ORIGINS=http://localhost:8000  # Same port
  # Remove REACT_APP_API_URL - not needed for unified app
```

**Access Points Change:**
- **Old Frontend**: `http://localhost:8002` ❌
- **New Frontend**: `http://localhost:8000` ✅
- **Old API**: `http://localhost:8001/api` ❌  
- **New API**: `http://localhost:8000/api` ✅

## Traefik Configuration Example

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.iptv.rule=Host(`iptv.example.com`)"
  - "traefik.http.services.iptv.loadbalancer.server.port=8000"
  # Single service - both frontend and API on port 8000
```

## Environment Variables

### Required
- `JWT_SECRET`: Your secret key for authentication
- `DATABASE_URL`: SQLite database path (default works fine)

### Optional
- `CORS_ORIGINS`: Allowed origins for API access
- `DEBUG`: Enable debug logging

### Not Needed
- ❌ `REACT_APP_API_URL`: Not used in unified architecture
- ❌ Separate frontend environment variables

## Summary

The "frontend connectivity issue" was actually a **configuration misunderstanding**. The application works correctly as a unified service on port 8000, serving both the React frontend and FastAPI backend from the same port.

**Key Points:**
- ✅ Single port (8000) serves everything
- ✅ Frontend accessible at root path (`/`)
- ✅ API accessible at `/api/*` prefix
- ✅ No separate frontend service needed
- ✅ Simplified Docker Compose configuration
