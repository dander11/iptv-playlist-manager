"""
Playlist management API routes
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel
import os
import shutil
from datetime import datetime

from core.database import get_db, Playlist, Channel
from core.auth import get_current_user, User
from core.config import get_settings
from services.m3u_parser import M3UParser

router = APIRouter()
settings = get_settings()
m3u_parser = M3UParser()


class PlaylistCreate(BaseModel):
    name: str
    description: Optional[str] = None
    source_url: Optional[str] = None


class PlaylistResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    source_url: Optional[str]
    source_file: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_validated: Optional[datetime]
    channel_count: int = 0
    
    class Config:
        from_attributes = True


class ChannelResponse(BaseModel):
    id: int
    name: str
    group_title: Optional[str]
    logo: Optional[str]
    tvg_id: Optional[str]
    tvg_name: Optional[str]
    tvg_logo: Optional[str]
    stream_url: str
    is_active: bool
    is_working: bool
    last_checked: Optional[datetime]
    response_time: Optional[float]
    
    class Config:
        from_attributes = True


@router.post("/", response_model=PlaylistResponse)
async def create_playlist(
    playlist_data: PlaylistCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new playlist from URL"""
    if not playlist_data.source_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Source URL is required"
        )
    
    # Create playlist record
    playlist = Playlist(
        name=playlist_data.name,
        description=playlist_data.description,
        source_url=playlist_data.source_url
    )
    
    db.add(playlist)
    db.commit()
    db.refresh(playlist)
    
    try:
        # Parse M3U from URL
        channels_data = m3u_parser.parse_m3u_from_url(playlist_data.source_url)
        
        # Save channels to database
        for channel_data in channels_data:
            channel = Channel(
                playlist_id=playlist.id,
                name=channel_data.get('name', 'Unknown'),
                group_title=channel_data.get('group_title', ''),
                logo=channel_data.get('logo', ''),
                tvg_id=channel_data.get('tvg_id', ''),
                tvg_name=channel_data.get('tvg_name', ''),
                tvg_logo=channel_data.get('tvg_logo', ''),
                tvg_epg=channel_data.get('tvg_epg', ''),
                stream_url=channel_data.get('stream_url', '')
            )
            db.add(channel)
        
        db.commit()
        
        # Get updated playlist with channel count
        playlist_response = db.query(Playlist).filter(Playlist.id == playlist.id).first()
        playlist_response.channel_count = len(channels_data)
        
        return playlist_response
        
    except Exception as e:
        # Clean up playlist if parsing failed
        db.delete(playlist)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error parsing M3U playlist: {str(e)}"
        )


@router.post("/upload", response_model=PlaylistResponse)
async def upload_playlist(
    name: str = Form(...),
    description: str = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload M3U playlist file"""
    
    # Validate file type
    if not file.filename.lower().endswith(('.m3u', '.m3u8')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only M3U and M3U8 files are allowed"
        )
    
    # Check file size
    if file.size > settings.max_playlist_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size: {settings.max_playlist_size} bytes"
        )
    
    # Create playlist record
    playlist = Playlist(
        name=name,
        description=description
    )
    
    db.add(playlist)
    db.commit()
    db.refresh(playlist)
    
    try:
        # Save uploaded file
        file_path = os.path.join(settings.uploads_dir, f"playlist_{playlist.id}_{file.filename}")
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        playlist.source_file = file_path
        db.commit()
        
        # Parse M3U from file
        channels_data = m3u_parser.parse_m3u_from_file(file_path)
        
        # Save channels to database
        for channel_data in channels_data:
            channel = Channel(
                playlist_id=playlist.id,
                name=channel_data.get('name', 'Unknown'),
                group_title=channel_data.get('group_title', ''),
                logo=channel_data.get('logo', ''),
                tvg_id=channel_data.get('tvg_id', ''),
                tvg_name=channel_data.get('tvg_name', ''),
                tvg_logo=channel_data.get('tvg_logo', ''),
                tvg_epg=channel_data.get('tvg_epg', ''),
                stream_url=channel_data.get('stream_url', '')
            )
            db.add(channel)
        
        db.commit()
        
        # Get updated playlist with channel count
        playlist_response = db.query(Playlist).filter(Playlist.id == playlist.id).first()
        playlist_response.channel_count = len(channels_data)
        
        return playlist_response
        
    except Exception as e:
        # Clean up playlist and file if parsing failed
        if playlist.source_file and os.path.exists(playlist.source_file):
            os.remove(playlist.source_file)
        db.delete(playlist)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error parsing M3U playlist: {str(e)}"
        )


@router.get("/", response_model=List[PlaylistResponse])
async def list_playlists(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    active_only: bool = True
):
    """List all playlists"""
    query = db.query(Playlist)
    
    if active_only:
        query = query.filter(Playlist.is_active == True)
    
    playlists = query.all()
    
    # Add channel counts
    for playlist in playlists:
        playlist.channel_count = db.query(Channel).filter(Channel.playlist_id == playlist.id).count()
    
    return playlists


@router.get("/{playlist_id}", response_model=PlaylistResponse)
async def get_playlist(
    playlist_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get playlist by ID"""
    playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()
    
    if not playlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Playlist not found"
        )
    
    # Add channel count
    playlist.channel_count = db.query(Channel).filter(Channel.playlist_id == playlist_id).count()
    
    return playlist


@router.get("/{playlist_id}/channels", response_model=List[ChannelResponse])
async def get_playlist_channels(
    playlist_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    active_only: bool = True,
    working_only: bool = False,
    group: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """Get channels from a playlist"""
    # Check if playlist exists
    playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()
    if not playlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Playlist not found"
        )
    
    query = db.query(Channel).filter(Channel.playlist_id == playlist_id)
    
    if active_only:
        query = query.filter(Channel.is_active == True)
    
    if working_only:
        query = query.filter(Channel.is_working == True)
    
    if group:
        query = query.filter(Channel.group_title == group)
    
    channels = query.offset(offset).limit(limit).all()
    return channels


@router.put("/{playlist_id}", response_model=PlaylistResponse)
async def update_playlist(
    playlist_id: int,
    playlist_data: PlaylistCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update playlist"""
    playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()
    
    if not playlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Playlist not found"
        )
    
    # Update playlist fields
    playlist.name = playlist_data.name
    playlist.description = playlist_data.description
    playlist.source_url = playlist_data.source_url
    playlist.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(playlist)
    
    return playlist


@router.delete("/{playlist_id}")
async def delete_playlist(
    playlist_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete playlist"""
    playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()
    
    if not playlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Playlist not found"
        )
    
    # Clean up uploaded file if exists
    if playlist.source_file and os.path.exists(playlist.source_file):
        os.remove(playlist.source_file)
    
    db.delete(playlist)
    db.commit()
    
    return {"message": "Playlist deleted successfully"}


@router.post("/{playlist_id}/refresh", response_model=PlaylistResponse)
async def refresh_playlist(
    playlist_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Refresh playlist from source URL"""
    playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()
    
    if not playlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Playlist not found"
        )
    
    if not playlist.source_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Playlist has no source URL to refresh from"
        )
    
    try:
        # Delete existing channels
        db.query(Channel).filter(Channel.playlist_id == playlist_id).delete()
        
        # Parse M3U from URL
        channels_data = m3u_parser.parse_m3u_from_url(playlist.source_url)
        
        # Save new channels to database
        for channel_data in channels_data:
            channel = Channel(
                playlist_id=playlist.id,
                name=channel_data.get('name', 'Unknown'),
                group_title=channel_data.get('group_title', ''),
                logo=channel_data.get('logo', ''),
                tvg_id=channel_data.get('tvg_id', ''),
                tvg_name=channel_data.get('tvg_name', ''),
                tvg_logo=channel_data.get('tvg_logo', ''),
                tvg_epg=channel_data.get('tvg_epg', ''),
                stream_url=channel_data.get('stream_url', '')
            )
            db.add(channel)
        
        playlist.updated_at = datetime.utcnow()
        db.commit()
        
        # Get updated playlist with channel count
        playlist.channel_count = len(channels_data)
        
        return playlist
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error refreshing playlist: {str(e)}"
        )
