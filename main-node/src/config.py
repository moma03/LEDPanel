"""
Pydantic settings loader for environment variables.
This file centralizes all configuration and makes the system portable.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from pathlib import Path

# Set .env file path
# env_path = Path(__file__).parent.parent / ".env"

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
    FETCH_INTERVAL_SECONDS: int = Field(60, env="FETCH_INTERVAL_SECONDS")

    # --- Logging ---
    LOG_LEVEL: str = Field("INFO", env="LOG_LEVEL")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()