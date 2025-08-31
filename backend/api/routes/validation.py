"""
Validation API routes
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from core.database import get_db, ValidationLog, ValidationResult, Playlist
from core.auth import get_current_user, User
from services.validation import ValidationService

router = APIRouter()
validation_service = ValidationService()


class ValidationLogResponse(BaseModel):
    id: int
    playlist_id: Optional[int]
    started_at: datetime
    completed_at: Optional[datetime]
    status: str
    total_channels: int
    working_channels: int
    failed_channels: int
    removed_channels: int
    duplicates_removed: int
    message: Optional[str]
    error_details: Optional[str]
    
    class Config:
        from_attributes = True


class ValidationResultResponse(BaseModel):
    id: int
    channel_id: int
    is_working: bool
    response_time: Optional[float]
    status_code: Optional[int]
    error_message: Optional[str]
    checked_at: datetime
    
    class Config:
        from_attributes = True


class ValidationRequest(BaseModel):
    playlist_ids: Optional[List[int]] = None
    validate_all: bool = False


@router.post("/validate")
async def trigger_validation(
    validation_request: ValidationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Trigger manual validation"""
    
    if validation_request.validate_all:
        # Validate all playlists
        background_tasks.add_task(validation_service.validate_all_playlists)
        return {"message": "Validation of all playlists started"}
    
    elif validation_request.playlist_ids:
        # Validate specific playlists
        for playlist_id in validation_request.playlist_ids:
            # Check if playlist exists
            playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()
            if not playlist:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Playlist {playlist_id} not found"
                )
            
            background_tasks.add_task(validation_service.validate_playlist, playlist_id)
        
        return {"message": f"Validation of {len(validation_request.playlist_ids)} playlists started"}
    
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either specify playlist_ids or set validate_all to true"
        )


@router.get("/logs", response_model=List[ValidationLogResponse])
async def get_validation_logs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    playlist_id: Optional[int] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """Get validation logs"""
    query = db.query(ValidationLog)
    
    if playlist_id:
        query = query.filter(ValidationLog.playlist_id == playlist_id)
    
    if status:
        query = query.filter(ValidationLog.status == status)
    
    logs = query.order_by(ValidationLog.started_at.desc()).offset(offset).limit(limit).all()
    return logs


@router.get("/logs/{log_id}", response_model=ValidationLogResponse)
async def get_validation_log(
    log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get specific validation log"""
    log = db.query(ValidationLog).filter(ValidationLog.id == log_id).first()
    
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Validation log not found"
        )
    
    return log


@router.get("/logs/{log_id}/results", response_model=List[ValidationResultResponse])
async def get_validation_results(
    log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    working_only: bool = False,
    failed_only: bool = False,
    limit: int = 100,
    offset: int = 0
):
    """Get validation results for a specific log"""
    # Check if log exists
    log = db.query(ValidationLog).filter(ValidationLog.id == log_id).first()
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Validation log not found"
        )
    
    query = db.query(ValidationResult).filter(ValidationResult.validation_log_id == log_id)
    
    if working_only:
        query = query.filter(ValidationResult.is_working == True)
    elif failed_only:
        query = query.filter(ValidationResult.is_working == False)
    
    results = query.offset(offset).limit(limit).all()
    return results


@router.get("/status")
async def get_validation_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current validation status"""
    
    # Get latest validation log
    latest_log = db.query(ValidationLog).order_by(ValidationLog.started_at.desc()).first()
    
    if not latest_log:
        return {
            "status": "never_run",
            "message": "No validations have been run yet"
        }
    
    # Get statistics from latest validation
    stats = {
        "status": latest_log.status,
        "last_run": latest_log.started_at,
        "completed_at": latest_log.completed_at,
        "total_channels": latest_log.total_channels,
        "working_channels": latest_log.working_channels,
        "failed_channels": latest_log.failed_channels,
        "removed_channels": latest_log.removed_channels,
        "duplicates_removed": latest_log.duplicates_removed
    }
    
    # Check if there are any running validations
    running_validations = db.query(ValidationLog).filter(ValidationLog.status == 'running').count()
    if running_validations > 0:
        stats["status"] = "running"
        stats["running_validations"] = running_validations
    
    return stats


@router.delete("/logs/{log_id}")
async def delete_validation_log(
    log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete validation log and its results"""
    log = db.query(ValidationLog).filter(ValidationLog.id == log_id).first()
    
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Validation log not found"
        )
    
    db.delete(log)
    db.commit()
    
    return {"message": "Validation log deleted successfully"}


@router.post("/generate-playlist")
async def generate_unified_playlist(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Generate unified M3U playlist from all working channels"""
    background_tasks.add_task(validation_service.generate_unified_playlist)
    return {"message": "Unified playlist generation started"}
