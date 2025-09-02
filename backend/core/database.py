"""
Database models and configuration
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
from datetime import datetime
import os
import logging
from pathlib import Path

from core.config import get_settings

logger = logging.getLogger(__name__)
Base = declarative_base()


class User(Base):
    """User model for authentication"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Playlist(Base):
    """Playlist model for storing playlist sources"""
    __tablename__ = "playlists"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    source_url = Column(String(500))  # URL if playlist is from web
    source_file = Column(String(255))  # File path if uploaded
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_validated = Column(DateTime)
    
    # Relationships
    channels = relationship("Channel", back_populates="playlist", cascade="all, delete-orphan")
    validation_logs = relationship("ValidationLog", back_populates="playlist")


class Channel(Base):
    """Channel model for individual IPTV channels"""
    __tablename__ = "channels"
    
    id = Column(Integer, primary_key=True, index=True)
    playlist_id = Column(Integer, ForeignKey("playlists.id"), nullable=False)
    
    # Channel metadata
    name = Column(String(200), nullable=False)
    group_title = Column(String(100))
    logo = Column(String(500))
    tvg_id = Column(String(100))
    tvg_name = Column(String(200))
    tvg_logo = Column(String(500))
    tvg_epg = Column(String(500))
    
    # Stream information
    stream_url = Column(String(1000), nullable=False)
    alternative_urls = Column(Text)  # JSON array of alternative URLs
    
    # Status tracking
    is_active = Column(Boolean, default=True)
    is_working = Column(Boolean, default=True)
    last_checked = Column(DateTime)
    check_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    response_time = Column(Float)  # Response time in seconds
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    playlist = relationship("Playlist", back_populates="channels")
    validation_results = relationship("ValidationResult", back_populates="channel")


class ValidationLog(Base):
    """Log entries for validation runs"""
    __tablename__ = "validation_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    playlist_id = Column(Integer, ForeignKey("playlists.id"))
    
    # Validation metadata
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    status = Column(String(50))  # 'running', 'completed', 'failed'
    
    # Statistics
    total_channels = Column(Integer, default=0)
    working_channels = Column(Integer, default=0)
    failed_channels = Column(Integer, default=0)
    removed_channels = Column(Integer, default=0)
    duplicates_removed = Column(Integer, default=0)
    
    # Details
    message = Column(Text)
    error_details = Column(Text)
    
    # Relationships
    playlist = relationship("Playlist", back_populates="validation_logs")
    validation_results = relationship("ValidationResult", back_populates="validation_log")


class ValidationResult(Base):
    """Individual channel validation results"""
    __tablename__ = "validation_results"
    
    id = Column(Integer, primary_key=True, index=True)
    validation_log_id = Column(Integer, ForeignKey("validation_logs.id"), nullable=False)
    channel_id = Column(Integer, ForeignKey("channels.id"), nullable=False)
    
    # Result details
    is_working = Column(Boolean)
    response_time = Column(Float)
    status_code = Column(Integer)
    error_message = Column(Text)
    checked_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    validation_log = relationship("ValidationLog", back_populates="validation_results")
    channel = relationship("Channel", back_populates="validation_results")


# Database setup
engine = None
SessionLocal = None


async def init_db():
    """Initialize database connection and create tables"""
    global engine, SessionLocal
    
    settings = get_settings()
    
    logger.info(f"Initializing database with URL: {settings.database_url}")
    logger.info(f"Current working directory: {os.getcwd()}")
    
    # Ensure database directory exists for SQLite
    if "sqlite" in settings.database_url:
        # Extract database path from URL
        db_url = settings.database_url.replace("sqlite:///", "").replace("sqlite://", "")
        
        # Handle different path formats
        if db_url.startswith("/"):
            # Absolute path
            db_path = Path(db_url)
        else:
            # Relative path - make it relative to current directory
            db_path = Path(os.getcwd()) / db_url
        
        # Ensure parent directory exists
        db_dir = db_path.parent
        try:
            db_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Ensured database directory exists: {db_dir}")
        except Exception as e:
            logger.error(f"Failed to create database directory {db_dir}: {e}")
            raise
        
        # Log detailed information
        logger.info(f"Database file path: {db_path}")
        logger.info(f"Database directory: {db_dir}")
        logger.info(f"Directory exists: {db_dir.exists()}")
        logger.info(f"Directory readable: {os.access(db_dir, os.R_OK) if db_dir.exists() else 'N/A'}")
        logger.info(f"Directory writable: {os.access(db_dir, os.W_OK) if db_dir.exists() else 'N/A'}")
        
        # Check if we can write to the directory
        if not os.access(db_dir, os.W_OK):
            error_msg = f"Database directory is not writable: {db_dir}"
            logger.error(error_msg)
            raise PermissionError(error_msg)
    
    try:
        # Create database engine
        engine = create_engine(
            settings.database_url,
            connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
        )
        
        # Create session factory
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        # Create tables
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        
        logger.info("Database initialized successfully")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        logger.error(f"Exception type: {type(e).__name__}")
        raise


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
