#!/usr/bin/env python3
"""
Application startup script with environment validation
"""

import os
import sys
import logging
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, '/app')

# Setup basic logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

def validate_environment():
    """Validate the container environment before starting the app"""
    logger.info("=== Environment Validation ===")
    
    # Check current user
    import pwd
    current_user = pwd.getpwuid(os.getuid()).pw_name
    logger.info(f"Running as user: {current_user}")
    
    # Check working directory
    cwd = os.getcwd()
    logger.info(f"Current working directory: {cwd}")
    logger.info(f"CWD readable: {os.access(cwd, os.R_OK)}")
    logger.info(f"CWD writable: {os.access(cwd, os.W_OK)}")
    
    # Check if we're in the app directory
    app_files = ['main.py', 'core', 'api']
    missing_files = [f for f in app_files if not os.path.exists(f)]
    if missing_files:
        logger.error(f"Missing application files: {missing_files}")
        return False
    
    logger.info("✅ Application files found")
    
    # Check frontend assets
    frontend_files = ['static/index.html', 'static/static']
    existing_frontend = [f for f in frontend_files if os.path.exists(f)]
    if existing_frontend:
        logger.info(f"✅ Frontend assets found: {existing_frontend}")
    else:
        logger.warning(f"⚠️ No frontend assets found. Expected: {frontend_files}")
        logger.warning("Application will run in API-only mode")
    
    # Check/create required directories
    required_dirs = ['data', 'logs', 'uploads', 'static']
    for directory in required_dirs:
        dir_path = Path(directory)
        try:
            dir_path.mkdir(exist_ok=True)
            if os.access(dir_path, os.W_OK):
                logger.info(f"✅ Directory {directory} is writable")
            else:
                logger.error(f"❌ Directory {directory} is not writable")
                return False
        except Exception as e:
            logger.error(f"❌ Failed to create/access directory {directory}: {e}")
            return False
    
    # Test database configuration
    try:
        from core.config import get_settings
        settings = get_settings()
        logger.info(f"Database URL: {settings.database_url}")
        
        # For SQLite, check if we can create the database file
        if "sqlite" in settings.database_url:
            from core.db_init import test_database_connection
            if not test_database_connection():
                logger.error("❌ Database connection test failed")
                return False
            logger.info("✅ Database connection test passed")
        
    except Exception as e:
        logger.error(f"❌ Configuration validation failed: {e}")
        return False
    
    logger.info("=== Environment validation completed successfully ===")
    return True

def main():
    """Main startup function"""
    logger.info("Starting IPTV Playlist Manager...")
    
    # Validate environment first
    if not validate_environment():
        logger.error("Environment validation failed. Exiting.")
        sys.exit(1)
    
    # Start the application
    try:
        import uvicorn
        from main import app
        
        logger.info("Starting uvicorn server...")
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            log_level="info"
        )
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
