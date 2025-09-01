"""
Core application configuration using Pydantic Settings
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator, computed_field
from typing import List, Union, Any
import os
import json


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # App configuration
    app_name: str = Field(default="IPTV Playlist Manager", description="Application name")
    debug: bool = Field(default=False, description="Debug mode")
    
    # Database configuration
    database_url: str = Field(
        default="sqlite:///./data/iptv.db",
        description="Database connection URL"
    )
    
    # Security configuration
    jwt_secret_key: str = Field(
        default="your-secret-key-change-this-in-production",
        description="JWT secret key for token signing"
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_expire_minutes: int = Field(default=30, description="JWT token expiration in minutes")
    
    # CORS configuration - stored as string and parsed to list
    cors_origins_raw: str = Field(
        default="*",
        description="Allowed CORS origins (raw)",
        alias="cors_origins"
    )
    
    @computed_field
    @property
    def cors_origins(self) -> List[str]:
        """Parse CORS origins from various formats"""
        value = self.cors_origins_raw
        
        if not value or value.strip() == "":
            return ["*"]
        
        value = value.strip()
        
        # Handle special case for wildcard
        if value == "*":
            return ["*"]
        
        # Try to parse as JSON array first
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return [str(item).strip() for item in parsed if item]
        except (json.JSONDecodeError, ValueError):
            pass
        
        # Parse as comma-separated string
        if "," in value:
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        
        # Single origin
        return [value] if value else ["*"]
    
    # Validation configuration
    validation_schedule: str = Field(
        default="0 2 * * *",  # Daily at 2 AM
        description="Cron expression for validation schedule"
    )
    validation_timeout: int = Field(
        default=30,
        description="Timeout for stream validation in seconds"
    )
    validation_concurrent_limit: int = Field(
        default=20,
        description="Maximum concurrent validations"
    )
    validation_retry_attempts: int = Field(
        default=3,
        description="Number of retry attempts for failed streams"
    )
    validation_retry_delay: int = Field(
        default=2,
        description="Delay between retry attempts in seconds"
    )
    
    # File paths
    data_dir: str = Field(default="./data", description="Data directory")
    logs_dir: str = Field(default="./logs", description="Logs directory")
    static_dir: str = Field(default="./static", description="Static files directory")
    uploads_dir: str = Field(default="./uploads", description="Upload directory")
    
    # Playlist configuration
    playlist_filename: str = Field(
        default="playlist.m3u",
        description="Output playlist filename"
    )
    max_playlist_size: int = Field(
        default=10 * 1024 * 1024,  # 10MB
        description="Maximum playlist file size in bytes"
    )
    
    # HTTP client configuration
    http_timeout: int = Field(default=30, description="HTTP request timeout")
    http_user_agent: str = Field(
        default="IPTV-Playlist-Manager/1.0",
        description="HTTP User-Agent header"
    )
    
    # Model configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


# Global settings instance
_settings = None


def get_settings() -> Settings:
    """Get application settings singleton"""
    global _settings
    if _settings is None:
        _settings = Settings()
        
        # Ensure directories exist
        os.makedirs(_settings.data_dir, exist_ok=True)
        os.makedirs(_settings.logs_dir, exist_ok=True)
        os.makedirs(_settings.static_dir, exist_ok=True)
        os.makedirs(_settings.uploads_dir, exist_ok=True)
    
    return _settings
