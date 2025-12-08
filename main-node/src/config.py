"""
Pydantic settings loader for environment variables.
This file centralizes all configuration and makes the system portable.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from pathlib import Path

class Settings(BaseSettings):
    # --- Database ---
    DATABASE_URL: str = Field(
        "sqlite+aiosqlite:///./data.db",
        env="DATABASE_URL"
    )

    # --- API Credentials (DB Timetables API) ---
    DB_API_KEY: str = Field(..., env="DB_API_KEY")
    DB_CLIENT_ID: str = Field(..., env="DB_CLIENT_ID")

    # --- Fetcher settings ---
    # Fetch application settings from settings.yaml 
    # TODO MAKE NOT SECURITY RELEVANT SETTINGS PART OF SETTINGS.YAML INSTEAD OF ENV FILE 
    FETCH_INTERVAL_SECONDS: int = Field(60, env="FETCH_INTERVAL_SECONDS")

    # --- Logging ---
    LOG_LEVEL: str = Field("INFO", env="LOG_LEVEL")

    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent.parent.parent / ".env",
        env_file_encoding="utf-8",
    )

settings = Settings()