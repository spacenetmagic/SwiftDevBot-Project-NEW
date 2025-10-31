#!/usr/bin/env python3
"""
Database initialization script.

Creates all tables and runs migrations.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from Systems.core.database import init_db, get_session_factory, get_engine
from Systems.core.logger import get_logger
from Systems.core.utils.config import get_config
import click


logger = get_logger(__name__)


async def initialize_database(force: bool = False) -> None:
    """
    Initialize database: create all tables.
    
    Args:
        force: If True, drop existing tables first (WARNING: destroys data!)
    """
    try:
        config = get_config()
        logger.info(f"Initializing database: {config.db_url}")
        
        engine = get_engine()
        
        if force:
            logger.warning("Force mode: dropping all existing tables!")
            if not click.confirm("This will delete all data. Continue?"):
                logger.info("Cancelled")
                return
            
            async with engine.begin() as conn:
                from Systems.core.database import Base
                await conn.run_sync(Base.metadata.drop_all)
                logger.info("All tables dropped")
        
        # Create all tables
        await init_db()
        logger.info("Database initialized successfully")
        
        # Verify tables were created
        async with engine.begin() as conn:
            from sqlalchemy import inspect
            inspector = inspect(engine.sync_engine)
            tables = inspector.get_table_names()
            logger.info(f"Created tables: {', '.join(tables)}")
        
        # Run migrations if using Alembic
        try:
            from alembic.config import Config as AlembicConfig
            from alembic import command
            
            alembic_cfg = AlembicConfig("alembic.ini")
            command.upgrade(alembic_cfg, "head")
            logger.info("Migrations applied successfully")
        except Exception as e:
            logger.warning(f"Migrations not applied: {e}")
            logger.info("If using Alembic, run: alembic upgrade head")
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}", exc_info=True)
        raise


async def check_database_connection() -> bool:
    """
    Check if database connection works.
    
    Returns:
        True if connection successful, False otherwise
    """
    try:
        async with get_session_factory()() as session:
            from sqlalchemy import text
            result = await session.execute(text("SELECT 1"))
            result.scalar()
            logger.info("Database connection successful")
            return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False


@click.command()
@click.option("--force", is_flag=True, help="Drop existing tables first (WARNING: destroys data!)")
@click.option("--check", is_flag=True, help="Only check database connection")
def main(force: bool, check: bool) -> None:
    """
    Initialize SwiftDevBot database.
    
    Creates all tables and runs migrations.
    """
    if check:
        success = asyncio.run(check_database_connection())
        sys.exit(0 if success else 1)
    
    try:
        asyncio.run(initialize_database(force=force))
        logger.info("✓ Database initialization complete")
    except Exception as e:
        logger.error(f"✗ Database initialization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

