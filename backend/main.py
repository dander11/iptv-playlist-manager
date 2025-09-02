"""
IPTV Playlist Manager Backend

A FastAPI-based backend for managing IPTV playlists with automated validation.
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import PlainTextResponse, FileResponse
import uvicorn
import os
from contextlib import asynccontextmanager
import logging
from datetime import datetime
from pathlib import Path

from api.routes import auth, playlists, channels, validation, system
from core.config import get_settings
from core.database import init_db
from core.scheduler import ValidationScheduler
from core.auth import get_current_user

# Configure logging
import os
os.makedirs('logs', exist_ok=True)  # Ensure logs directory exists

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
    
    try:
        # Ensure data directories exist
        from core.db_init import ensure_data_directories
        ensure_data_directories()
        
        # Initialize database
        await init_db()
        
        # Start validation scheduler
        scheduler = ValidationScheduler()
        scheduler.start()
        
        # Verify static file mounting
        logger.info("=== Static File Mounting Verification ===")
        static_dir = Path("static")
        if static_dir.exists():
            # Check what's actually mounted
            react_static = static_dir / "static"
            if react_static.exists():
                css_files = list(react_static.rglob("*.css"))
                js_files = list(react_static.rglob("*.js"))
                logger.info(f"React static structure detected:")
                logger.info(f"  CSS files: {[f.name for f in css_files[:3]]}")  # Show first 3
                logger.info(f"  JS files: {[f.name for f in js_files[:3]]}")   # Show first 3
                
                if css_files or js_files:
                    logger.info("✅ Static assets should be accessible at /static/css/ and /static/js/")
                else:
                    logger.warning("⚠️ No CSS/JS files found in nested static directory")
            else:
                logger.info("No nested static directory found")
        
        logger.info("Application startup completed successfully")
        
    except Exception as e:
        logger.error(f"Application startup failed: {e}")
        logger.error(f"Exception type: {type(e).__name__}")
        raise  # Re-raise to fail startup
    
    yield
    
    # Shutdown
    logger.info("Shutting down IPTV Playlist Manager")
    try:
        scheduler.stop()
    except:
        pass


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

# Include routers with /api prefix
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(playlists.router, prefix="/api/playlists", tags=["playlists"])
app.include_router(channels.router, prefix="/api/channels", tags=["channels"])
app.include_router(validation.router, prefix="/api/validation", tags=["validation"])
app.include_router(system.router, prefix="/api/system", tags=["system"])

# Mount static files for React frontend
if not os.path.exists("static"):
    os.makedirs("static")

# Log the static directory structure for debugging
logger.info("=== Static Directory Analysis ===")
static_path = Path("static")
if static_path.exists():
    logger.info(f"Static directory exists: {static_path.absolute()}")
    
    # Check for React build structure
    index_html = static_path / "index.html"
    react_static = static_path / "static"
    
    logger.info(f"index.html exists: {index_html.exists()}")
    logger.info(f"Nested static/ directory exists: {react_static.exists()}")
    
    if react_static.exists():
        logger.info("Detected React build with nested static directory")
        # List contents of nested static directory
        for item in react_static.iterdir():
            logger.info(f"  Found: {item.name}")
            if item.is_dir():
                for subitem in item.iterdir():
                    logger.info(f"    {item.name}/{subitem.name}")
    
    # List all files for debugging
    all_files = list(static_path.rglob("*"))
    logger.info(f"Total files in static/: {len([f for f in all_files if f.is_file()])}")

# Mount static files with enhanced React build support
react_static_dir = Path("static") / "static"
regular_static_dir = Path("static")

# Enhanced detection for React build structure
react_css_dir = react_static_dir / "css"
react_js_dir = react_static_dir / "js"
has_react_assets = react_css_dir.exists() or react_js_dir.exists()

# Also check if nested static directory contains any files (fallback detection)
nested_has_files = False
if react_static_dir.exists():
    nested_files = list(react_static_dir.rglob("*.css")) + list(react_static_dir.rglob("*.js"))
    nested_has_files = len(nested_files) > 0
    logger.info(f"Nested static directory has {len(nested_files)} CSS/JS files")

logger.info(f"React static detection: css_dir={react_css_dir.exists()}, js_dir={react_js_dir.exists()}, has_assets={has_react_assets}, nested_has_files={nested_has_files}")

if react_static_dir.exists() and (has_react_assets or nested_has_files):
    # React build creates nested static/ directory with CSS/JS folders
    # Mount the nested directory to /static so CSS/JS are accessible at expected paths
    app.mount("/static", StaticFiles(directory=str(react_static_dir)), name="static")
    logger.info(f"✅ Mounted React nested static files from: {react_static_dir}")
    logger.info(f"   CSS files accessible at: /static/css/")
    logger.info(f"   JS files accessible at: /static/js/")
    
    # Also mount the parent static directory for other assets (manifest, favicon, etc.)
    try:
        app.mount("/assets", StaticFiles(directory="static"), name="assets")
        logger.info("✅ Mounted parent static directory as /assets")
    except Exception as e:
        logger.warning(f"Could not mount parent static directory: {e}")
        
elif regular_static_dir.exists():
    # Check if assets exist directly in static/ (css/, js/ folders)
    css_dir = regular_static_dir / "css"
    js_dir = regular_static_dir / "js"
    
    if css_dir.exists() or js_dir.exists():
        # Direct static structure - mount the static directory
        app.mount("/static", StaticFiles(directory="static"), name="static")
        logger.info("✅ Mounted static files from: static (direct structure)")
    else:
        # Check if we have a React build but no assets detected
        if (regular_static_dir / "index.html").exists():
            # We have a React build, mount it anyway and let it serve what it can
            app.mount("/static", StaticFiles(directory="static"), name="static")
            logger.warning("⚠️ React build detected but no CSS/JS assets found - mounting anyway")
        else:
            # Create default static mount to prevent errors
            app.mount("/static", StaticFiles(directory="static"), name="static")
            logger.info("✅ Mounted static directory (may be empty)")
else:
    # Ensure static directory exists and mount it
    regular_static_dir.mkdir(exist_ok=True)
    app.mount("/static", StaticFiles(directory="static"), name="static")
    logger.warning("⚠️ Created and mounted empty static directory")

# Also mount any additional static directories that might exist
additional_static_dirs = ["assets", "public", "dist"]
for dirname in additional_static_dirs:
    if os.path.exists(dirname):
        app.mount(f"/{dirname}", StaticFiles(directory=dirname), name=dirname)
        logger.info(f"✅ Mounted additional static directory: {dirname}")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "IPTV Playlist Manager"}


@app.get("/api")
async def api_root():
    """API root endpoint with available endpoints"""
    return {
        "message": "IPTV Playlist Manager API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
        "endpoints": {
            "authentication": "/api/auth",
            "playlists": "/api/playlists", 
            "channels": "/api/channels",
            "validation": "/api/validation",
            "system": "/api/system"
        },
        "resources": {
            "openapi_schema": "/openapi.json",
            "playlist_download": "/playlist.m3u"
        }
    }


@app.get("/api/info")
async def api_info():
    """Get API information and server status"""
    from core.database import engine
    
    return {
        "service": "IPTV Playlist Manager API",
        "version": "1.0.0",
        "status": "running",
        "database": {
            "url": settings.database_url,
            "connected": engine is not None
        },
        "configuration": {
            "cors_origins": settings.cors_origins,
            "debug_mode": settings.debug,
            "validation_timeout": settings.validation_timeout
        }
    }


@app.get("/api/health/frontend")
async def frontend_health_check():
    """Comprehensive frontend health check"""
    from core.frontend_validator import validate_frontend_assets, validate_index_html_asset_references
    
    try:
        asset_results = validate_frontend_assets()
        html_results = validate_index_html_asset_references()
        
        return {
            "status": "healthy" if asset_results["frontend_available"] and html_results["all_references_valid"] else "degraded",
            "frontend_available": asset_results["frontend_available"],
            "index_html_exists": asset_results["index_html_exists"],
            "static_mount_path": asset_results["static_mount_path"],
            "assets_found": len(asset_results["assets_found"]),
            "asset_references_valid": html_results["all_references_valid"],
            "issues": asset_results["issues"] + html_results["issues"],
            "recommendations": asset_results["recommendations"]
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "frontend_available": False
        }


@app.get("/api/debug/static")
async def debug_static_structure():
    """Debug endpoint to show static file structure and test accessibility"""
    try:
        import os
        from pathlib import Path
        
        static_path = Path("static")
        structure = {
            "working_directory": str(Path.cwd()),
            "static_exists": static_path.exists(),
            "static_absolute_path": str(static_path.absolute()),
            "files": [],
            "directories": [],
            "mounting_test": {}
        }
        
        if static_path.exists():
            # List all files and directories recursively
            for item in static_path.rglob("*"):
                relative_path = str(item.relative_to(static_path))
                if item.is_file():
                    structure["files"].append({
                        "path": relative_path,
                        "size": item.stat().st_size,
                        "accessible_url": f"/static/{relative_path}"
                    })
                elif item.is_dir():
                    structure["directories"].append(relative_path)
            
            # Test if we can find CSS/JS files for mounting verification
            css_files = list(static_path.rglob("*.css"))
            js_files = list(static_path.rglob("*.js"))
            
            structure["mounting_test"] = {
                "css_files_found": [str(f.relative_to(static_path)) for f in css_files[:5]],
                "js_files_found": [str(f.relative_to(static_path)) for f in js_files[:5]],
                "react_nested_structure": (static_path / "static").exists(),
                "recommended_mount": "static/static" if (static_path / "static" / "css").exists() or len([f for f in css_files if "static/css" in str(f)]) > 0 else "static"
            }
        
        return structure
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/status")
async def api_status():
    """Quick API status check"""
    return {
        "status": "online",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "service": "IPTV Playlist Manager"
    }


@app.get("/playlist.m3u", response_class=PlainTextResponse)
async def get_playlist():
    """Serve the unified M3U playlist"""
    try:
        with open("static/playlist.m3u", "r", encoding="utf-8") as f:
            content = f.read()
        return content
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Playlist not found")


@app.get("/{full_path:path}")
async def serve_react_app(full_path: str):
    """
    Serve React frontend for all non-API routes
    This implements client-side routing for the React SPA
    """
    # Serve index.html for all frontend routes
    index_path = "static/index.html"
    if os.path.exists(index_path):
        return FileResponse(index_path)
    else:
        # Fallback if no frontend build exists
        return {"message": "IPTV Playlist Manager API", "docs": "/docs", "note": "Frontend not available"}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
