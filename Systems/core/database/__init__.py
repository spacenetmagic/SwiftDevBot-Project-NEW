"""
Database package for SwiftDevBot.

Provides database connection, session management, and base models.
"""

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from Systems.core.logger import get_logger
from Systems.core.utils.config import get_config


logger = get_logger(__name__)


class Base(DeclarativeBase):
    """Base class for all database models."""
    
    pass


# Global engine and session factory
_engine = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine():
    """
    Get or create async database engine.
    
    Returns:
        AsyncEngine instance
    """
    global _engine
    
    if _engine is None:
        config = get_config()
        logger.info(f"Creating database engine: {config.db_url}")
        
        # Different engine configs for different database types
        if config.db_type == "sqlite" or config.db_type == "memory":
            # SQLite doesn't support pool_pre_ping and some other PostgreSQL features
            _engine = create_async_engine(
                config.db_url,
                echo=False,  # Set to True for SQL query logging
                connect_args={"check_same_thread": False} if config.db_type == "sqlite" else {},
            )
        else:  # PostgreSQL
            _engine = create_async_engine(
                config.db_url,
                echo=False,  # Set to True for SQL query logging
                pool_pre_ping=True,  # Verify connections before using
                pool_size=10,
                max_overflow=20,
                pool_recycle=3600,  # Recycle connections after 1 hour
            )
        
        logger.info("Database engine created successfully")
    
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """
    Get or create async session factory.
    
    Returns:
        AsyncSessionmaker instance
    """
    global _session_factory
    
    if _session_factory is None:
        engine = get_engine()
        _session_factory = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )
        logger.info("Session factory created successfully")
    
    return _session_factory


async def get_db() -> AsyncSession:
    """
    Dependency injection function for getting database session.
    
    Usage:
        async with get_db() as session:
            # Use session here
            pass
    
    Yields:
        AsyncSession instance
    """
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize database: create all tables.
    
    This should be called once at application startup.
    """
    logger.info("Initializing database...")
    engine = get_engine()
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("Database initialized successfully")


async def close_db() -> None:
    """
    Close database connections.
    
    This should be called at application shutdown.
    """
    global _engine, _session_factory
    
    logger.info("Closing database connections...")
    
    if _engine:
        await _engine.dispose()
        _engine = None
    
    _session_factory = None
    logger.info("Database connections closed")

