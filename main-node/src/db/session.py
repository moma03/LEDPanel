"""Async SQLAlchemy engine + session factory + database initialization."""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from .models import Base
from ..config import settings

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,  # set to True for SQL debug logs
    future=True,
)

# Session factory
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def init_db():
    """Initialize DB (WAL mode for SQLite + create tables)."""
    async with engine.begin() as conn:
        # Enable Write-Ahead Logging in SQLite for better concurrency
        await conn.execute(text("PRAGMA journal_mode=WAL;"))
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)