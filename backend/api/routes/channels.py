"""
Channel management API routes
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from core.database import get_db, Channel, Playlist
from core.auth import get_current_user, User

router = APIRouter()


class ChannelUpdate(BaseModel):
    name: Optional[str] = None
    group_title: Optional[str] = None
    logo: Optional[str] = None
    tvg_id: Optional[str] = None
    tvg_name: Optional[str] = None
    tvg_logo: Optional[str] = None
    tvg_epg: Optional[str] = None
    stream_url: Optional[str] = None
    is_active: Optional[bool] = None


class ChannelResponse(BaseModel):
    id: int
    playlist_id: int
    name: str
    group_title: Optional[str]
    logo: Optional[str]
    tvg_id: Optional[str]
    tvg_name: Optional[str]
    tvg_logo: Optional[str]
    tvg_epg: Optional[str]
    stream_url: str
    alternative_urls: Optional[str]
    is_active: bool
    is_working: bool
    last_checked: Optional[datetime]
    check_count: int
    failure_count: int
    response_time: Optional[float]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


@router.get("/", response_model=List[ChannelResponse])
async def list_channels(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    playlist_id: Optional[int] = None,
    group_title: Optional[str] = None,
    active_only: bool = True,
    working_only: bool = False,
    search: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """List channels with filtering options"""
    query = db.query(Channel)
    
    if playlist_id:
        query = query.filter(Channel.playlist_id == playlist_id)
    
    if group_title:
        query = query.filter(Channel.group_title == group_title)
    
    if active_only:
        query = query.filter(Channel.is_active == True)
    
    if working_only:
        query = query.filter(Channel.is_working == True)
    
    if search:
        query = query.filter(Channel.name.ilike(f"%{search}%"))
    
    channels = query.offset(offset).limit(limit).all()
    return channels


@router.get("/{channel_id}", response_model=ChannelResponse)
async def get_channel(
    channel_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get channel by ID"""
    channel = db.query(Channel).filter(Channel.id == channel_id).first()
    
    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Channel not found"
        )
    
    return channel


@router.put("/{channel_id}", response_model=ChannelResponse)
async def update_channel(
    channel_id: int,
    channel_data: ChannelUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update channel"""
    channel = db.query(Channel).filter(Channel.id == channel_id).first()
    
    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Channel not found"
        )
    
    # Update fields that were provided
    for field, value in channel_data.model_dump(exclude_unset=True).items():
        setattr(channel, field, value)
    
    channel.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(channel)
    
    return channel


@router.delete("/{channel_id}")
async def delete_channel(
    channel_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete channel"""
    channel = db.query(Channel).filter(Channel.id == channel_id).first()
    
    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Channel not found"
        )
    
    db.delete(channel)
    db.commit()
    
    return {"message": "Channel deleted successfully"}


@router.get("/groups/", response_model=List[str])
async def list_channel_groups(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    playlist_id: Optional[int] = None
):
    """Get list of unique channel groups"""
    query = db.query(Channel.group_title).distinct()
    
    if playlist_id:
        query = query.filter(Channel.playlist_id == playlist_id)
    
    groups = query.filter(Channel.group_title.isnot(None)).all()
    return [group[0] for group in groups if group[0]]


@router.get("/stats/", response_model=dict)
async def get_channel_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    playlist_id: Optional[int] = None
):
    """Get channel statistics"""
    query = db.query(Channel)
    
    if playlist_id:
        query = query.filter(Channel.playlist_id == playlist_id)
    
    total_channels = query.count()
    active_channels = query.filter(Channel.is_active == True).count()
    working_channels = query.filter(Channel.is_working == True).count()
    
    # Group statistics
    group_query = query.filter(Channel.group_title.isnot(None))
    groups = db.execute(
        """
        SELECT group_title, COUNT(*) as count
        FROM channels
        WHERE group_title IS NOT NULL
        {} 
        GROUP BY group_title
        ORDER BY count DESC
        """.format("AND playlist_id = :playlist_id" if playlist_id else ""),
        {"playlist_id": playlist_id} if playlist_id else {}
    ).fetchall()
    
    group_stats = [{"name": group[0], "count": group[1]} for group in groups]
    
    return {
        "total_channels": total_channels,
        "active_channels": active_channels,
        "working_channels": working_channels,
        "inactive_channels": total_channels - active_channels,
        "broken_channels": active_channels - working_channels,
        "groups": group_stats
    }
