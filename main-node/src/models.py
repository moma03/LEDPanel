"""
Data models for the fetching application using Pydantic v2.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class StationData(BaseModel):
    """Information about a station."""
    eva: int = Field(..., description="EVA number (unique station identifier)")
    name: str = Field(..., description="Station name")
    ds100: Optional[str] = Field(None, description="DS100 code")
    platforms: int = Field(default=0, description="Number of platforms")
    
    class Config:
        frozen = True


class PlannedEvent(BaseModel):
    """A planned departure or arrival event."""
    stop_id: str = Field(..., description="Stop identifier")
    event_type: str = Field(..., description="'arrival' or 'departure'")
    planned_time: datetime = Field(..., description="Planned time")
    planned_platform: Optional[str] = Field(None, description="Planned platform")
    planned_path: Optional[str] = Field(None, description="Planned path (ppth) - pipe-separated stations")
    wings: Optional[str] = Field(None, description="Wing identifiers if train has wings (wings)")
    category: Optional[str] = Field(None, description="Train category from trip label (tl.c), e.g., ICE/RE/RB")
    train_number: Optional[str] = Field(None, description="Train number from trip label (tl.n)")
    operator: Optional[str] = Field(None, description="Operator/owner code from trip label (tl.o)")
    hidden: Optional[bool] = Field(None, description="Hidden flag (hi='1' means hidden)")
    
    class Config:
        frozen = True


class ChangedEvent(BaseModel):
    """A changed (actual) departure or arrival event."""
    stop_id: str = Field(..., description="Stop identifier")
    event_type: str = Field(..., description="'arrival' or 'departure'")
    changed_time: Optional[datetime] = Field(None, description="Actual time")
    changed_platform: Optional[str] = Field(None, description="Actual platform")
    changed_path: Optional[str] = Field(None, description="Changed path (cpth) - pipe-separated stations")
    changed_status: Optional[str] = Field(None, description="Status code")
    fetched_at: datetime = Field(default_factory=datetime.utcnow, description="When this was fetched")
    wings: Optional[str] = Field(None, description="Wing identifiers if present")
    category: Optional[str] = Field(None, description="Train category from trip label (tl.c)")
    train_number: Optional[str] = Field(None, description="Train number from trip label (tl.n)")
    operator: Optional[str] = Field(None, description="Operator/owner code from trip label (tl.o)")
    hidden: Optional[bool] = Field(None, description="Hidden flag (hi)")
    
    class Config:
        frozen = True


class FetchStats(BaseModel):
    """Statistics about a fetch operation."""
    operation: str = Field(..., description="Name of the operation")
    success: bool = Field(..., description="Was it successful?")
    records_fetched: int = Field(default=0, description="Number of records fetched")
    duration_ms: float = Field(..., description="Duration in milliseconds")
    error: Optional[str] = Field(None, description="Error message if failed")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
