"""
Automated validation scheduler using background tasks
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional
from threading import Thread, Event
import schedule
import time

from core.config import get_settings
from services.validation import ValidationService

logger = logging.getLogger(__name__)


class ValidationScheduler:
    """Handles scheduled validation tasks"""
    
    def __init__(self):
        self.settings = get_settings()
        self.validation_service = ValidationService()
        self._stop_event = Event()
        self._thread: Optional[Thread] = None
        self._running = False
    
    def start(self):
        """Start the validation scheduler"""
        if self._running:
            logger.warning("Scheduler is already running")
            return
        
        self._running = True
        self._stop_event.clear()
        
        # Schedule validation based on cron expression
        # For now, we'll use a simplified daily schedule at 2 AM
        schedule.every().day.at("02:00").do(self._run_validation)
        
        # Start background thread
        self._thread = Thread(target=self._run_scheduler, daemon=True)
        self._thread.start()
        
        logger.info("Validation scheduler started")
    
    def stop(self):
        """Stop the validation scheduler"""
        if not self._running:
            return
        
        self._running = False
        self._stop_event.set()
        
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=10)
        
        schedule.clear()
        logger.info("Validation scheduler stopped")
    
    def _run_scheduler(self):
        """Background scheduler loop"""
        logger.info("Scheduler thread started")
        
        while not self._stop_event.is_set():
            try:
                schedule.run_pending()
                # Check every minute
                if self._stop_event.wait(timeout=60):
                    break
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                # Continue running despite errors
                if self._stop_event.wait(timeout=60):
                    break
        
        logger.info("Scheduler thread stopped")
    
    def _run_validation(self):
        """Run validation task"""
        logger.info("Starting scheduled validation")
        
        try:
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Run validation
            loop.run_until_complete(self.validation_service.validate_all_playlists())
            
            logger.info("Scheduled validation completed successfully")
            
        except Exception as e:
            logger.error(f"Scheduled validation failed: {e}")
        finally:
            loop.close()
    
    def trigger_validation(self):
        """Trigger immediate validation"""
        logger.info("Triggering immediate validation")
        
        # Run in background thread to avoid blocking
        thread = Thread(target=self._run_validation, daemon=True)
        thread.start()
    
    @property
    def is_running(self) -> bool:
        """Check if scheduler is running"""
        return self._running
    
    def get_next_run_time(self) -> Optional[datetime]:
        """Get next scheduled run time"""
        if not schedule.jobs:
            return None
        
        next_run = schedule.next_run()
        return next_run if next_run else None
