"""
Stream validation service for checking IPTV channel availability
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import aiohttp
import requests
from sqlalchemy.orm import Session
from sqlalchemy import and_

from core.config import get_settings
from core.database import get_db, Playlist, Channel, ValidationLog, ValidationResult
from services.m3u_parser import M3UParser

logger = logging.getLogger(__name__)


class ValidationService:
    """Service for validating IPTV streams"""
    
    def __init__(self):
        self.settings = get_settings()
        self.m3u_parser = M3UParser()
    
    async def validate_stream_url(self, url: str, timeout: int = None) -> Tuple[bool, float, Optional[str], Optional[int]]:
        """
        Validate a single stream URL
        Returns: (is_working, response_time, error_message, status_code)
        """
        if not url or not url.strip():
            return False, 0.0, "Empty URL", None
        
        timeout = timeout or self.settings.validation_timeout
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=timeout),
                headers={'User-Agent': self.settings.http_user_agent}
            ) as session:
                
                # First try HEAD request for faster check
                try:
                    async with session.head(url) as response:
                        response_time = time.time() - start_time
                        
                        if response.status in [200, 302, 301]:
                            return True, response_time, None, response.status
                        else:
                            return False, response_time, f"HTTP {response.status}", response.status
                            
                except aiohttp.ClientError:
                    # If HEAD fails, try GET with limited content
                    pass
                
                # Fall back to GET request with range header
                try:
                    headers = {
                        'User-Agent': self.settings.http_user_agent,
                        'Range': 'bytes=0-1023'  # Only get first 1KB
                    }
                    
                    async with session.get(url, headers=headers) as response:
                        response_time = time.time() - start_time
                        
                        if response.status in [200, 206, 302, 301]:  # 206 for partial content
                            return True, response_time, None, response.status
                        else:
                            return False, response_time, f"HTTP {response.status}", response.status
                            
                except Exception as e:
                    response_time = time.time() - start_time
                    return False, response_time, str(e), None
                    
        except asyncio.TimeoutError:
            response_time = time.time() - start_time
            return False, response_time, "Request timeout", None
        except Exception as e:
            response_time = time.time() - start_time
            return False, response_time, str(e), None
    
    async def validate_channels_batch(self, channels: List[Channel], semaphore: asyncio.Semaphore) -> List[Dict[str, Any]]:
        """Validate a batch of channels concurrently"""
        tasks = []
        
        for channel in channels:
            task = self._validate_single_channel(channel, semaphore)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and return valid results
        valid_results = []
        for result in results:
            if not isinstance(result, Exception):
                valid_results.append(result)
            else:
                logger.error(f"Channel validation error: {result}")
        
        return valid_results
    
    async def _validate_single_channel(self, channel: Channel, semaphore: asyncio.Semaphore) -> Dict[str, Any]:
        """Validate a single channel with concurrency control"""
        async with semaphore:
            logger.debug(f"Validating channel: {channel.name} ({channel.stream_url})")
            
            # Try main URL
            is_working, response_time, error_message, status_code = await self.validate_stream_url(
                channel.stream_url
            )
            
            # If main URL fails, try alternative URLs
            if not is_working and channel.alternative_urls:
                try:
                    import json
                    alt_urls = json.loads(channel.alternative_urls)
                    
                    for alt_url in alt_urls:
                        alt_working, alt_response_time, alt_error, alt_status = await self.validate_stream_url(alt_url)
                        if alt_working:
                            # Use the working alternative URL
                            is_working = True
                            response_time = alt_response_time
                            error_message = None
                            status_code = alt_status
                            # Update the main URL to the working alternative
                            channel.stream_url = alt_url
                            break
                except Exception as e:
                    logger.error(f"Error processing alternative URLs for channel {channel.id}: {e}")
            
            return {
                'channel_id': channel.id,
                'channel_name': channel.name,
                'stream_url': channel.stream_url,
                'is_working': is_working,
                'response_time': response_time,
                'error_message': error_message,
                'status_code': status_code,
                'checked_at': datetime.utcnow()
            }
    
    async def validate_playlist(self, playlist_id: int) -> Dict[str, Any]:
        """Validate all channels in a playlist"""
        logger.info(f"Starting validation for playlist {playlist_id}")
        
        # Get database session
        db = next(get_db())
        
        try:
            # Get playlist and channels
            playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()
            if not playlist:
                raise ValueError(f"Playlist {playlist_id} not found")
            
            channels = db.query(Channel).filter(
                and_(Channel.playlist_id == playlist_id, Channel.is_active == True)
            ).all()
            
            if not channels:
                logger.warning(f"No active channels found in playlist {playlist_id}")
                return {
                    'playlist_id': playlist_id,
                    'total_channels': 0,
                    'working_channels': 0,
                    'failed_channels': 0,
                    'results': []
                }
            
            # Create validation log entry
            validation_log = ValidationLog(
                playlist_id=playlist_id,
                started_at=datetime.utcnow(),
                status='running',
                total_channels=len(channels)
            )
            db.add(validation_log)
            db.commit()
            db.refresh(validation_log)
            
            # Create semaphore for concurrency control
            semaphore = asyncio.Semaphore(self.settings.validation_concurrent_limit)
            
            # Validate channels in batches
            batch_size = 50
            all_results = []
            
            for i in range(0, len(channels), batch_size):
                batch = channels[i:i + batch_size]
                logger.info(f"Validating batch {i//batch_size + 1}/{(len(channels)-1)//batch_size + 1}")
                
                batch_results = await self.validate_channels_batch(batch, semaphore)
                all_results.extend(batch_results)
                
                # Save intermediate results
                self._save_validation_results(db, validation_log.id, batch_results)
            
            # Update channel status in database
            working_count = 0
            failed_count = 0
            
            for result in all_results:
                channel = db.query(Channel).filter(Channel.id == result['channel_id']).first()
                if channel:
                    channel.is_working = result['is_working']
                    channel.last_checked = result['checked_at']
                    channel.check_count += 1
                    channel.response_time = result['response_time']
                    
                    if result['is_working']:
                        working_count += 1
                        channel.failure_count = 0  # Reset failure count on success
                    else:
                        failed_count += 1
                        channel.failure_count += 1
                        
                        # Mark as inactive if failed too many times
                        if channel.failure_count >= self.settings.validation_retry_attempts:
                            channel.is_active = False
                            logger.info(f"Marking channel {channel.name} as inactive after {channel.failure_count} failures")
            
            # Update validation log
            validation_log.completed_at = datetime.utcnow()
            validation_log.status = 'completed'
            validation_log.working_channels = working_count
            validation_log.failed_channels = failed_count
            validation_log.message = f"Validated {len(all_results)} channels"
            
            # Update playlist last validated timestamp
            playlist.last_validated = datetime.utcnow()
            
            db.commit()
            
            logger.info(f"Validation completed for playlist {playlist_id}: {working_count} working, {failed_count} failed")
            
            return {
                'playlist_id': playlist_id,
                'validation_log_id': validation_log.id,
                'total_channels': len(all_results),
                'working_channels': working_count,
                'failed_channels': failed_count,
                'results': all_results
            }
            
        except Exception as e:
            # Update validation log with error
            if 'validation_log' in locals():
                validation_log.completed_at = datetime.utcnow()
                validation_log.status = 'failed'
                validation_log.error_details = str(e)
                db.commit()
            
            logger.error(f"Validation failed for playlist {playlist_id}: {e}")
            raise
        finally:
            db.close()
    
    def _save_validation_results(self, db: Session, validation_log_id: int, results: List[Dict[str, Any]]):
        """Save validation results to database"""
        for result in results:
            validation_result = ValidationResult(
                validation_log_id=validation_log_id,
                channel_id=result['channel_id'],
                is_working=result['is_working'],
                response_time=result['response_time'],
                status_code=result.get('status_code'),
                error_message=result.get('error_message'),
                checked_at=result['checked_at']
            )
            db.add(validation_result)
        
        db.commit()
    
    async def validate_all_playlists(self) -> List[Dict[str, Any]]:
        """Validate all active playlists"""
        logger.info("Starting validation of all playlists")
        
        db = next(get_db())
        
        try:
            # Get all active playlists
            playlists = db.query(Playlist).filter(Playlist.is_active == True).all()
            
            if not playlists:
                logger.info("No active playlists found")
                return []
            
            results = []
            
            for playlist in playlists:
                try:
                    result = await self.validate_playlist(playlist.id)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Failed to validate playlist {playlist.id}: {e}")
                    results.append({
                        'playlist_id': playlist.id,
                        'error': str(e)
                    })
            
            # Generate updated unified playlist
            await self.generate_unified_playlist()
            
            logger.info(f"Completed validation of {len(playlists)} playlists")
            return results
            
        finally:
            db.close()
    
    async def generate_unified_playlist(self):
        """Generate unified M3U playlist from all working channels"""
        logger.info("Generating unified playlist")
        
        db = next(get_db())
        
        try:
            # Get all working channels from active playlists
            channels = db.query(Channel).join(Playlist).filter(
                and_(
                    Channel.is_active == True,
                    Channel.is_working == True,
                    Playlist.is_active == True
                )
            ).all()
            
            # Convert to M3U format
            channel_data = []
            for channel in channels:
                channel_dict = {
                    'name': channel.name,
                    'stream_url': channel.stream_url,
                    'group_title': channel.group_title or 'General',
                    'tvg_id': channel.tvg_id or '',
                    'tvg_name': channel.tvg_name or channel.name,
                    'tvg_logo': channel.tvg_logo or channel.logo or '',
                    'tvg_epg': channel.tvg_epg or ''
                }
                channel_data.append(channel_dict)
            
            # Deduplicate channels
            channel_data = self.m3u_parser.deduplicate_channels(channel_data)
            
            # Generate and save M3U file
            playlist_path = f"{self.settings.static_dir}/{self.settings.playlist_filename}"
            self.m3u_parser.save_m3u_file(channel_data, playlist_path)
            
            logger.info(f"Generated unified playlist with {len(channel_data)} channels at {playlist_path}")
            
        finally:
            db.close()
