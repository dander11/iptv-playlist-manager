"""
System and configuration API routes
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import os
import psutil
from datetime import datetime

from core.database import get_db, Playlist, Channel, ValidationLog
from core.auth import get_current_user, get_current_admin_user, User
from core.config import get_settings
from core.scheduler import ValidationScheduler

router = APIRouter()
settings = get_settings()


class SystemStatus(BaseModel):
    status: str
    uptime: str
    memory_usage: dict
    disk_usage: dict
    database_stats: dict
    scheduler_status: dict


class ConfigUpdate(BaseModel):
    validation_schedule: Optional[str] = None
    validation_timeout: Optional[int] = None
    validation_concurrent_limit: Optional[int] = None
    validation_retry_attempts: Optional[int] = None


@router.get("/health")
async def health_check():
    """Basic health check"""
    return {"status": "healthy", "timestamp": datetime.utcnow()}


@router.get("/status", response_model=SystemStatus)
async def get_system_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get comprehensive system status"""
    
    # System information
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # Database statistics
    total_playlists = db.query(Playlist).count()
    active_playlists = db.query(Playlist).filter(Playlist.is_active == True).count()
    total_channels = db.query(Channel).count()
    working_channels = db.query(Channel).filter(Channel.is_working == True).count()
    validation_logs = db.query(ValidationLog).count()
    
    # Scheduler status
    scheduler = ValidationScheduler()
    
    return {
        "status": "healthy",
        "uptime": str(datetime.utcnow()),
        "memory_usage": {
            "total": memory.total,
            "used": memory.used,
            "available": memory.available,
            "percentage": memory.percent
        },
        "disk_usage": {
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
            "percentage": (disk.used / disk.total) * 100
        },
        "database_stats": {
            "total_playlists": total_playlists,
            "active_playlists": active_playlists,
            "total_channels": total_channels,
            "working_channels": working_channels,
            "validation_logs": validation_logs
        },
        "scheduler_status": {
            "is_running": scheduler.is_running,
            "next_run": scheduler.get_next_run_time()
        }
    }


@router.get("/config")
async def get_configuration(
    current_user: User = Depends(get_current_admin_user)
):
    """Get current system configuration"""
    return {
        "validation_schedule": settings.validation_schedule,
        "validation_timeout": settings.validation_timeout,
        "validation_concurrent_limit": settings.validation_concurrent_limit,
        "validation_retry_attempts": settings.validation_retry_attempts,
        "validation_retry_delay": settings.validation_retry_delay,
        "max_playlist_size": settings.max_playlist_size,
        "playlist_filename": settings.playlist_filename,
        "http_timeout": settings.http_timeout,
        "jwt_expire_minutes": settings.jwt_expire_minutes
    }


@router.put("/config")
async def update_configuration(
    config_update: ConfigUpdate,
    current_user: User = Depends(get_current_admin_user)
):
    """Update system configuration (admin only)"""
    
    # For now, return the current settings
    # In a production system, you might want to save these to a database
    # or configuration file and restart services as needed
    
    updated_fields = []
    
    for field, value in config_update.model_dump(exclude_unset=True).items():
        if hasattr(settings, field):
            setattr(settings, field, value)
            updated_fields.append(field)
    
    return {
        "message": f"Configuration updated: {', '.join(updated_fields)}",
        "updated_fields": updated_fields
    }


@router.get("/logs")
async def get_system_logs(
    current_user: User = Depends(get_current_admin_user),
    log_type: str = "app",
    lines: int = 100
):
    """Get system logs"""
    
    log_files = {
        "app": f"{settings.logs_dir}/app.log",
        "validation": f"{settings.logs_dir}/validation.log"
    }
    
    if log_type not in log_files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid log type. Available types: {list(log_files.keys())}"
        )
    
    log_file = log_files[log_type]
    
    if not os.path.exists(log_file):
        return {"logs": [], "message": f"Log file {log_file} not found"}
    
    try:
        # Read last N lines from log file
        with open(log_file, 'r') as f:
            all_lines = f.readlines()
            recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
        
        return {
            "logs": [line.strip() for line in recent_lines],
            "total_lines": len(all_lines),
            "returned_lines": len(recent_lines)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error reading log file: {str(e)}"
        )


@router.post("/maintenance/cleanup")
async def cleanup_old_data(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
    days_old: int = 30
):
    """Clean up old validation logs and results"""
    from datetime import timedelta
    
    cutoff_date = datetime.utcnow() - timedelta(days=days_old)
    
    # Delete old validation logs (this will cascade to results)
    deleted_logs = db.query(ValidationLog).filter(
        ValidationLog.started_at < cutoff_date
    ).delete()
    
    db.commit()
    
    return {
        "message": f"Cleaned up {deleted_logs} validation logs older than {days_old} days"
    }


@router.post("/maintenance/vacuum")
async def vacuum_database(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Vacuum SQLite database to reclaim space"""
    try:
        db.execute("VACUUM")
        db.commit()
        return {"message": "Database vacuum completed successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database vacuum failed: {str(e)}"
        )


@router.get("/version")
async def get_version():
    """Get application version information"""
    return {
        "name": "IPTV Playlist Manager",
        "version": "1.0.0",
        "build_date": "2024-01-01",
        "python_version": "3.9+",
        "api_version": "v1"
    }
