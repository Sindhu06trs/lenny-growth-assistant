from typing import AsyncGenerator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
    AsyncEngine,
)
from app.core.config import settings
from app.core.logging_config import logger

# Lazy engine creation
_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    """
    Returns or initializes the global AsyncEngine instance.
    """
    global _engine
    if _engine is None:
        db_url = settings.async_database_url
        logger.info(f"Initializing Async Database Engine: {settings.get_safe_database_url()}")
        
        # SQLite vs PostgreSQL connection options
        if db_url.startswith("sqlite"):
            _engine = create_async_engine(
                db_url,
                echo=False,
                future=True,
            )
        else:
            _engine = create_async_engine(
                db_url,
                echo=False,
                pool_size=settings.DB_POOL_SIZE,
                max_overflow=settings.DB_MAX_OVERFLOW,
                pool_timeout=settings.DB_POOL_TIMEOUT,
                pool_pre_ping=True,
                future=True,
            )
    return _engine


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    """
    Returns or initializes the async session factory.
    """
    global _sessionmaker
    if _sessionmaker is None:
        _sessionmaker = async_sessionmaker(
            bind=get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
    return _sessionmaker


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency yielding an AsyncSession.
    Automatically commits successful transactions and rolls back on failure.
    """
    session_factory = get_sessionmaker()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


from contextlib import asynccontextmanager

@asynccontextmanager
async def get_async_session_context() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager yielding an AsyncSession for background scripts, CLI commands, and tasks.
    """
    session_factory = get_sessionmaker()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def check_db_connection() -> dict:
    """
    Tests database connectivity safely without exposing credentials.
    Returns dictionary with status and database dialect.
    """
    try:
        engine = get_engine()
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            dialect = engine.dialect.name
            return {
                "status": "connected",
                "database": dialect,
                "detail": "Database connection verified successfully."
            }
    except Exception as e:
        logger.warning(f"Database connection check failed: {type(e).__name__}")
        return {
            "status": "disconnected",
            "database": "unknown",
            "detail": "Database is not reachable. Ensure PostgreSQL is running and credentials in .env are valid."
        }
