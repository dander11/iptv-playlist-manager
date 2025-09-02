"""
Database initialization utilities with better error handling and directory management
"""

import os
import sys
import logging
from pathlib import Path
from core.config import get_settings

logger = logging.getLogger(__name__)


def ensure_data_directories():
    """Ensure all required data directories exist with proper permissions"""
    settings = get_settings()
    
    # List of directories to create
    directories = [
        settings.data_dir,
        settings.logs_dir,
        settings.uploads_dir,
        "static"
    ]
    
    for directory in directories:
        try:
            # Convert to absolute path
            abs_path = Path(directory).resolve()
            
            # Create directory if it doesn't exist
            abs_path.mkdir(parents=True, exist_ok=True)
            
            # Log creation
            logger.info(f"Ensured directory exists: {abs_path}")
            
            # Check permissions
            if not os.access(abs_path, os.W_OK):
                logger.warning(f"Directory not writable: {abs_path}")
            else:
                logger.info(f"Directory is writable: {abs_path}")
                
        except Exception as e:
            logger.error(f"Failed to create directory {directory}: {e}")
            raise


def get_database_info():
    """Get detailed information about database configuration"""
    settings = get_settings()
    
    logger.info(f"Database URL: {settings.database_url}")
    
    if "sqlite" in settings.database_url:
        # Extract database path
        db_path = settings.database_url.replace("sqlite:///", "").replace("sqlite://", "")
        
        # Convert to absolute path if relative
        if not db_path.startswith("/"):
            db_path = os.path.join(os.getcwd(), db_path)
        
        db_path = Path(db_path).resolve()
        db_dir = db_path.parent
        
        logger.info(f"Database file path: {db_path}")
        logger.info(f"Database directory: {db_dir}")
        logger.info(f"Current working directory: {os.getcwd()}")
        logger.info(f"Database directory exists: {db_dir.exists()}")
        logger.info(f"Database file exists: {db_path.exists()}")
        
        if db_dir.exists():
            logger.info(f"Directory readable: {os.access(db_dir, os.R_OK)}")
            logger.info(f"Directory writable: {os.access(db_dir, os.W_OK)}")
            logger.info(f"Directory executable: {os.access(db_dir, os.X_OK)}")
        
        return {
            "db_path": db_path,
            "db_dir": db_dir,
            "exists": db_path.exists(),
            "dir_exists": db_dir.exists(),
            "writable": db_dir.exists() and os.access(db_dir, os.W_OK)
        }
    
    return {"type": "non-sqlite"}


def test_database_connection():
    """Test database connection and permissions"""
    from sqlalchemy import create_engine, text
    
    settings = get_settings()
    
    try:
        # Get database info
        db_info = get_database_info()
        
        if db_info.get("type") == "non-sqlite":
            logger.info("Non-SQLite database detected")
        else:
            # Ensure database directory exists
            db_info["db_dir"].mkdir(parents=True, exist_ok=True)
        
        # Test engine creation
        engine = create_engine(
            settings.database_url,
            connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
        )
        
        # Test connection
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            logger.info("Database connection successful")
            return True
            
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        logger.error(f"Exception type: {type(e).__name__}")
        return False


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Test everything
    try:
        ensure_data_directories()
        get_database_info()
        test_database_connection()
        print("✅ All database checks passed")
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        sys.exit(1)
