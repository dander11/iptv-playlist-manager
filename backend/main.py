"""
IPTV Playlist Manager Backend

A FastAPI-based backend for managing IPTV playlists with automated validation.
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import PlainTextResponse
import uvicorn
import os
from contextlib import asynccontextmanager
import logging

from api.routes import auth, playlists, channels, validation, system
from core.config import get_settings
from core.database import init_db
from core.scheduler import ValidationScheduler
from core.auth import get_current_user

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - startup and shutdown"""
    # Startup
    logger.info("Starting IPTV Playlist Manager")
    
    # Initialize database
    await init_db()
    
    # Start validation scheduler
    scheduler = ValidationScheduler()
    scheduler.start()
    
    yield
    
    # Shutdown
    logger.info("Shutting down IPTV Playlist Manager")
    scheduler.stop()


# Create FastAPI app
app = FastAPI(
    title="IPTV Playlist Manager",
    description="Manage, aggregate, and validate IPTV playlists",
    version="1.0.0",
    lifespan=lifespan
)

# Get settings
settings = get_settings()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(playlists.router, prefix="/api/playlists", tags=["playlists"])
app.include_router(channels.router, prefix="/api/channels", tags=["channels"])
app.include_router(validation.router, prefix="/api/validation", tags=["validation"])
app.include_router(system.router, prefix="/api/system", tags=["system"])

# Mount static files
if not os.path.exists("static"):
    os.makedirs("static")
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "IPTV Playlist Manager"}


@app.get("/playlist.m3u", response_class=PlainTextResponse)
async def get_playlist():
    """Serve the unified M3U playlist"""
    try:
        with open("static/playlist.m3u", "r", encoding="utf-8") as f:
            content = f.read()
        return content
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Playlist not found")


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "IPTV Playlist Manager API", "docs": "/docs"}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
