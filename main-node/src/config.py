"""
Pydantic settings loader for environment variables and JSON config.
This file centralizes all configuration and makes the system portable.

Sensitive data (API keys, passwords) comes from .env file.
Application settings come from settings.json file.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, model_validator
from pathlib import Path
from typing import Optional, List
import json

class Settings(BaseSettings):
    # --- Sensitive data from .env ---
    DATABASE_URL: str = Field(
        "sqlite+aiosqlite:///./data.db",
        description="Database connection URL"
    )
    DB_API_KEY: str = Field(..., description="DB Timetables API key")
    DB_CLIENT_ID: str = Field(..., description="DB Timetables client ID")
    
    # --- Application settings (loaded from settings.json or defaults) ---
    LOOKAHEAD_HOURS: int = Field(
        2,
        description="Number of hours to look ahead for fetching data"
    )
    LOOKBEHIND_HOURS: int = Field(
        0,
        description="Number of hours to look behind for fetching data if initial empty"
    )
    STATIONS: List[int] = Field(
        default_factory=list,
        description="List of station EVA identifiers to monitor"
    )
    FETCH_INTERVAL_SECONDS: int = Field(
        60,
        description="Interval between fetch cycles in seconds"
    )
    PLANNED_FETCH_INTERVAL_SECONDS: int = Field(
        3600,
        description="Interval between planned events fetches (seconds). Default 1 hour"
    )
    RETRY_ATTEMPTS: int = Field(
        3,
        description="Number of retry attempts for failed requests"
    )
    TIMEOUT_SECONDS: int = Field(
        30,
        description="Timeout duration for API requests in seconds"
    )
    
    # --- Logging ---
    LOG_LEVEL: str = Field("INFO", description="Logging level")
    LOG_FILE_PATH: Optional[str] = Field(
        None,
        description="File path for storing log files (None = stdout only)"
    )
    
    # --- Settings file control ---
    SETTINGS_FILE_PATH: Path = Field(
        default_factory=lambda: Path(__file__).parent.parent / "settings.json",
        description="Path to settings.json file"
    )

    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent.parent.parent / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @model_validator(mode='after')
    def load_from_json(self):
        """Load non-sensitive settings from settings.json if it exists."""
        settings_file = self.SETTINGS_FILE_PATH
        
        if settings_file.exists():
            try:
                with open(settings_file, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                
                # Map JSON keys to Settings fields (if not already set by env vars)
                json_mapping = {
                    'lookahead_hours': 'LOOKAHEAD_HOURS',
                    'lookbehind_hours': 'LOOKBEHIND_HOURS',
                    'stations': 'STATIONS',
                    'fetch_interval_seconds': 'FETCH_INTERVAL_SECONDS',
                    'retry_attempts': 'RETRY_ATTEMPTS',
                    'timeout_seconds': 'TIMEOUT_SECONDS',
                    'log_level': 'LOG_LEVEL',
                    'log_file_path': 'LOG_FILE_PATH',
                }
                
                # Update settings from JSON (only if not explicitly set via env)
                for json_key, field_name in json_mapping.items():
                    if json_key in json_data:
                        setattr(self, field_name, json_data[json_key])
                        
            except json.JSONDecodeError as e:
                print(f"Warning: Could not parse {settings_file}: {e}")
            except Exception as e:
                print(f"Warning: Error loading {settings_file}: {e}")
        
        return self


settings = Settings()