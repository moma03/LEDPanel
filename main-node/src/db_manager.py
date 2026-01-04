"""
Database Manager module for persistent storage and retrieval.
Uses SQLAlchemy async ORM with PostgreSQL backend and connection pooling.
Handles all database operations with retry logic.
"""

from datetime import datetime, timedelta
from typing import List, Optional, AsyncGenerator
from contextlib import asynccontextmanager
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, DateTime

from .logger import setup_logger
from .exceptions import DatabaseError, retry_with_backoff
from .models import StationData, PlannedEvent, ChangedEvent
from .config import settings

logger = setup_logger(__name__)

Base = declarative_base()


# ============================================================================
# SQLAlchemy ORM Models
# ============================================================================

class DBStation(Base):
    """Persistent station metadata."""
    __tablename__ = "stations"
    
    eva = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    ds100 = Column(String(10), nullable=True, unique=True)
    platforms = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DBPlannedEvent(Base):
    """Planned departures/arrivals."""
    __tablename__ = "planned_events"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    stop_id = Column(String(100), nullable=False, unique=True)
    eva = Column(Integer, nullable=False)
    event_type = Column(String(10), nullable=False)  # 'arrival' or 'departure'
    planned_time = Column(DateTime, nullable=False)
    planned_platform = Column(String(10), nullable=True)
    planned_path = Column(String(1000), nullable=True)
    wings = Column(String(500), nullable=True)
    planned_line = Column(String(200), nullable=True)
    planned_destination = Column(String(500), nullable=True)
    category = Column(String(20), nullable=True)
    train_number = Column(String(20), nullable=True)
    operator = Column(String(50), nullable=True)
    hidden = Column(sa.Boolean, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (sa.Index("idx_eva_planned_time", "eva", "planned_time"),)


class DBChangedEvent(Base):
    """Actual arrivals/departures (real-time updates)."""
    __tablename__ = "changed_events"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    stop_id = Column(String(100), nullable=False)
    eva = Column(Integer, nullable=False)
    event_type = Column(String(10), nullable=False)  # 'arrival' or 'departure'
    changed_time = Column(DateTime, nullable=True)
    changed_platform = Column(String(10), nullable=True)
    changed_status = Column(String(10), nullable=True)  # 'p', 'a', 'c'
    changed_path = Column(String(1000), nullable=True)
    changed_line = Column(String(200), nullable=True)
    changed_destination = Column(String(500), nullable=True)
    category = Column(String(20), nullable=True)
    train_number = Column(String(20), nullable=True)
    operator = Column(String(50), nullable=True)
    hidden = Column(sa.Boolean, nullable=True)
    wings = Column(String(500), nullable=True)
    fetched_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (sa.Index("idx_eva_fetched", "eva", "fetched_at"),)


# ============================================================================
# Database Manager
# ============================================================================

class DatabaseManager:
    """Manages database connections and operations with async support."""
    
    def __init__(self):
        """Initialize database manager with connection settings."""
        self.db_url = settings.DATABASE_URL
        self._engine = None
        self._session_factory = None
    
    async def _ensure_initialized(self):
        """Lazily initialize engine and session factory on first use."""
        if self._engine is None:
            # Convert postgres:// to postgresql+asyncpg:// for async
            db_url = self.db_url.replace("postgres://", "postgresql+asyncpg://")
            
            self._engine = create_async_engine(
                db_url,
                echo=False,
                pool_size=20,
                max_overflow=10,
                pool_pre_ping=True,  # Verify connections before use
                pool_recycle=3600,   # Recycle connections after 1 hour
            )
            
            self._session_factory = async_sessionmaker(
                self._engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )
            
            # Create tables if they don't exist
            async with self._engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
                logger.info("Database schema initialized")
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Context manager for database sessions."""
        await self._ensure_initialized()
        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                raise
    
    @retry_with_backoff(operation_name="check_connection")
    async def check_connection(self) -> bool:
        """
        Test database connection.
        
        Returns:
            True if connection successful, False otherwise
        
        Raises:
            DatabaseError: If connection check fails after retries
        """
        try:
            logger.info("Checking database connection...")
            async with self.get_session() as session:
                await session.execute(sa.text("SELECT 1"))
            logger.info("Database connection successful")
            return True
        except Exception as e:
            logger.error(f"Database connection check failed: {e}")
            raise DatabaseError(f"Connection check failed: {e}") from e
    
    @retry_with_backoff(operation_name="has_station_data")
    async def has_station_data(self, eva: int) -> bool:
        """
        Check if station data exists in database.
        
        Args:
            eva: EVA station identifier
        
        Returns:
            True if station data exists, False otherwise
        
        Raises:
            DatabaseError: If query fails after retries
        """
        try:
            logger.debug(f"Checking if station {eva} exists in database")
            
            async with self.get_session() as session:
                result = await session.execute(
                    sa.select(DBStation).where(DBStation.eva == eva)
                )
                return result.scalars().first() is not None
        
        except Exception as e:
            logger.error(f"Error checking station data: {e}")
            raise DatabaseError(f"Failed to check station data: {e}") from e
    
    @retry_with_backoff(operation_name="save_station_data")
    async def save_station_data(self, station: StationData) -> bool:
        """
        Save or update station information.
        
        Args:
            station: StationData object to save
        
        Returns:
            True if successful
        
        Raises:
            DatabaseError: If save fails after retries
        """
        try:
            logger.debug(f"Saving station data for {station.name} (EVA {station.eva})")
            
            async with self.get_session() as session:
                # Upsert: check if exists, update or insert
                result = await session.execute(
                    sa.select(DBStation).where(DBStation.eva == station.eva)
                )
                existing = result.scalars().first()
                
                if existing:
                    # Update
                    existing.name = station.name
                    existing.ds100 = station.ds100
                    existing.platforms = station.platforms
                    existing.updated_at = datetime.utcnow()
                else:
                    # Insert
                    new_station = DBStation(
                        eva=station.eva,
                        name=station.name,
                        ds100=station.ds100,
                        platforms=station.platforms,
                    )
                    session.add(new_station)
            
            return True
        
        except Exception as e:
            logger.error(f"Error saving station data: {e}")
            raise DatabaseError(f"Failed to save station data: {e}") from e
    
    @retry_with_backoff(operation_name="has_planned_events_for_interval")
    async def has_planned_events_for_interval(
        self,
        eva: int,
        start_time: datetime,
        end_time: datetime
    ) -> bool:
        """
        Check if planned events exist for the given interval.
        
        Args:
            eva: EVA station identifier
            start_time: Start of interval
            end_time: End of interval
        
        Returns:
            True if planned events exist for the interval
        
        Raises:
            DatabaseError: If query fails after retries
        """
        try:
            logger.debug(f"Checking planned events for station {eva} in interval")
            
            async with self.get_session() as session:
                result = await session.execute(
                    sa.select(sa.func.count(DBPlannedEvent.id)).where(
                        (DBPlannedEvent.eva == eva) &
                        (DBPlannedEvent.planned_time >= start_time) &
                        (DBPlannedEvent.planned_time <= end_time)
                    )
                )
                count = result.scalar() or 0
                return count > 0
        
        except Exception as e:
            logger.error(f"Error checking planned events: {e}")
            raise DatabaseError(f"Failed to check planned events: {e}") from e
    
    @retry_with_backoff(operation_name="save_planned_events")
    async def save_planned_events(self, eva: int, events: List[PlannedEvent]) -> int:
        """
        Save planned events to database, avoiding duplicates.
        Uses upsert (insert on conflict update) on stop_id.
        
        Args:
            eva: EVA station identifier
            events: List of PlannedEvent objects
        
        Returns:
            Number of events saved
        
        Raises:
            DatabaseError: If save fails after retries
        """
        try:
            if not events:
                return 0
            
            logger.debug(f"Saving {len(events)} planned events for station {eva}")
            
            async with self.get_session() as session:
                for event in events:
                    # Try to get existing
                    result = await session.execute(
                        sa.select(DBPlannedEvent).where(
                            DBPlannedEvent.stop_id == event.stop_id
                        )
                    )
                    existing = result.scalars().first()
                    
                    if existing:
                        # Update only if new time is more recent
                        if event.planned_time > existing.planned_time:
                            existing.planned_time = event.planned_time
                            existing.planned_platform = event.planned_platform
                            existing.planned_path = getattr(event, 'planned_path', None)
                            existing.wings = getattr(event, 'wings', None)
                            existing.planned_line = getattr(event, 'planned_line', None)
                            existing.planned_destination = getattr(event, 'planned_destination', None)
                            existing.category = getattr(event, 'category', None)
                            existing.train_number = getattr(event, 'train_number', None)
                            existing.operator = getattr(event, 'operator', None)
                            existing.hidden = getattr(event, 'hidden', None)
                    else:
                        # Insert new
                        db_event = DBPlannedEvent(
                            stop_id=event.stop_id,
                            eva=eva,
                            event_type=event.event_type,
                            planned_time=event.planned_time,
                            planned_platform=event.planned_platform,
                            planned_path=getattr(event, 'planned_path', None),
                            wings=getattr(event, 'wings', None),
                            planned_line=getattr(event, 'planned_line', None),
                            planned_destination=getattr(event, 'planned_destination', None),
                            category=getattr(event, 'category', None),
                            train_number=getattr(event, 'train_number', None),
                            operator=getattr(event, 'operator', None),
                            hidden=getattr(event, 'hidden', None),
                        )
                        session.add(db_event)
            
            return len(events)
        
        except Exception as e:
            logger.error(f"Error saving planned events: {e}")
            raise DatabaseError(f"Failed to save planned events: {e}") from e
    
    @retry_with_backoff(operation_name="save_changed_events")
    async def save_changed_events(self, eva: int, events: List[ChangedEvent]) -> int:
        """
        Save changed events (actual arrivals/departures) to database.
        These represent real-time updates and are always appended (not deduplicated).
        
        Args:
            eva: EVA station identifier
            events: List of ChangedEvent objects
        
        Returns:
            Number of events saved
        
        Raises:
            DatabaseError: If save fails after retries
        """
        try:
            if not events:
                return 0
            
            logger.debug(f"Saving {len(events)} changed events for station {eva}")
            
            async with self.get_session() as session:
                for event in events:
                    # Always insert (don't deduplicate for real-time data)
                    db_event = DBChangedEvent(
                        stop_id=event.stop_id,
                        eva=eva,
                        event_type=event.event_type,
                        changed_time=event.changed_time,
                        changed_platform=event.changed_platform,
                        changed_path=getattr(event, 'changed_path', None),
                        changed_line=getattr(event, 'changed_line', None),
                        changed_destination=getattr(event, 'changed_destination', None),
                        category=getattr(event, 'category', None),
                        train_number=getattr(event, 'train_number', None),
                        operator=getattr(event, 'operator', None),
                        hidden=getattr(event, 'hidden', None),
                        wings=getattr(event, 'wings', None),
                        changed_status=event.changed_status,
                        fetched_at=event.fetched_at or datetime.utcnow(),
                    )
                    session.add(db_event)
            
            return len(events)
        
        except Exception as e:
            logger.error(f"Error saving changed events: {e}")
            raise DatabaseError(f"Failed to save changed events: {e}") from e
    
    @retry_with_backoff(operation_name="get_delayed_trains_without_plan")
    async def get_delayed_trains_without_plan(
        self,
        eva: int,
        lookback_hours: int = 2
    ) -> List[str]:
        """
        Get list of train stop IDs that are delayed but have no planned data in DB.
        Used to identify trains where we need to fetch additional plan data.
        
        Args:
            eva: EVA station identifier
            lookback_hours: How far back to look for delays
        
        Returns:
            List of stop IDs to fetch plans for
        
        Raises:
            DatabaseError: If query fails after retries
        """
        try:
            logger.debug(f"Finding delayed trains without plan for station {eva}")
            
            cutoff_time = datetime.utcnow() - timedelta(hours=lookback_hours)
            
            async with self.get_session() as session:
                # Find changed events without corresponding planned events
                result = await session.execute(
                    sa.select(DBChangedEvent.stop_id).distinct().where(
                        (DBChangedEvent.eva == eva) &
                        (DBChangedEvent.fetched_at >= cutoff_time) &
                        ~sa.exists(
                            sa.select(1).where(
                                DBPlannedEvent.stop_id == DBChangedEvent.stop_id
                            )
                        )
                    )
                )
                
                stop_ids = result.scalars().all()
                
                if stop_ids:
                    logger.debug(f"Found {len(stop_ids)} delayed trains without plan")
                
                return list(stop_ids)
        
        except Exception as e:
            logger.error(f"Error getting delayed trains: {e}")
            raise DatabaseError(f"Failed to get delayed trains: {e}") from e
    
    async def close(self):
        """Close database connection pool."""
        if self._engine:
            await self._engine.dispose()
            logger.info("Database connections closed")


# Global instance
db = DatabaseManager()
