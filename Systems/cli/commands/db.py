"""
CLI commands for database management.
"""

import asyncio
import sys
from pathlib import Path

import click

from Systems.core.database import close_db, get_engine, get_session_factory, init_db
from Systems.core.logger import get_logger
from Systems.core.utils.config import get_config
from sqlalchemy import text

logger = get_logger(__name__)


@click.group(name="db")
def db_group() -> None:
    """Database management commands."""
    pass


@db_group.command("init")
@click.option("--force", is_flag=True, help="Drop existing tables first (WARNING: destroys data!)")
def init(force: bool) -> None:
    """
    Initialize database: create all tables.
    
    Args:
        force: If True, drop existing tables first (WARNING: destroys data!)
    
    Example:
        sdb db init
        sdb db init --force
    """
    try:
        async def _init_db() -> None:
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
                click.echo(f"✓ Created {len(tables)} tables: {', '.join(tables)}")
            
            # Run migrations if using Alembic
            try:
                from alembic.config import Config as AlembicConfig
                from alembic import command
                
                alembic_cfg = AlembicConfig("alembic.ini")
                command.upgrade(alembic_cfg, "head")
                logger.info("Migrations applied successfully")
                click.echo("✓ Migrations applied successfully")
            except Exception as e:
                logger.warning(f"Migrations not applied: {e}")
                click.echo(f"⚠ Migrations not applied: {e}")
                click.echo("If using Alembic, run: alembic upgrade head")
        
        asyncio.run(_init_db())
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}", exc_info=True)
        click.echo(f"✗ Error: {str(e)}", err=True)
        sys.exit(1)


@db_group.command("check")
def check() -> None:
    """
    Check database connection.
    
    Example:
        sdb db check
    """
    try:
        async def _check_db() -> bool:
            try:
                async with get_session_factory()() as session:
                    result = await session.execute(text("SELECT 1"))
                    result.scalar()
                    return True
            except Exception as e:
                logger.error(f"Database connection failed: {e}")
                return False
        
        success = asyncio.run(_check_db())
        
        if success:
            config = get_config()
            click.echo(f"✓ Database connection successful: {config.db_url}")
            sys.exit(0)
        else:
            click.echo("✗ Database connection failed", err=True)
            sys.exit(1)
        
    except Exception as e:
        logger.error(f"Failed to check database: {e}", exc_info=True)
        click.echo(f"✗ Error: {str(e)}", err=True)
        sys.exit(1)


@db_group.command("migrate")
@click.argument("action", type=click.Choice(["upgrade", "downgrade", "history", "current"]), default="upgrade")
@click.option("--revision", default="head", help="Revision to migrate to")
def migrate(action: str, revision: str) -> None:
    """
    Run database migrations (Alembic).
    
    Args:
        action: Migration action (upgrade, downgrade, history, current)
        revision: Revision to migrate to (default: head)
    
    Examples:
        sdb db migrate upgrade
        sdb db migrate upgrade --revision abc123
        sdb db migrate downgrade --revision -1
        sdb db migrate history
        sdb db migrate current
    """
    try:
        from alembic.config import Config as AlembicConfig
        from alembic import command
        
        alembic_cfg = AlembicConfig("alembic.ini")
        
        if action == "upgrade":
            command.upgrade(alembic_cfg, revision)
            click.echo(f"✓ Database upgraded to: {revision}")
        elif action == "downgrade":
            command.downgrade(alembic_cfg, revision)
            click.echo(f"✓ Database downgraded to: {revision}")
        elif action == "history":
            command.history(alembic_cfg)
        elif action == "current":
            command.current(alembic_cfg)
        
    except FileNotFoundError:
        click.echo("✗ Error: alembic.ini not found. Is Alembic configured?", err=True)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)
        click.echo(f"✗ Error: {str(e)}", err=True)
        sys.exit(1)


@db_group.command("info")
def info() -> None:
    """
    Show database information.
    
    Example:
        sdb db info
    """
    try:
        async def _show_info() -> None:
            config = get_config()
            
            click.echo("Database Information:")
            click.echo("")
            click.echo(f"  Type: {config.db_type}")
            click.echo(f"  URL: {config.db_url}")
            
            if config.db_type == "postgresql":
                click.echo(f"  Host: {config.db_host}")
                click.echo(f"  Port: {config.db_port}")
                click.echo(f"  Database: {config.db_name}")
                click.echo(f"  User: {config.db_user}")
            elif config.db_type == "sqlite":
                click.echo(f"  Path: {config.db_path}")
            
            # Check connection
            try:
                async with get_session_factory()() as session:
                    result = await session.execute(text("SELECT version()"))
                    version = result.scalar()
                    click.echo(f"  Version: {version}")
                    click.echo("")
                    click.echo("✓ Connection: OK")
            except Exception as e:
                click.echo("")
                click.echo(f"✗ Connection: Failed ({e})")
            
            # Show tables
            try:
                engine = get_engine()
                async with engine.begin() as conn:
                    from sqlalchemy import inspect
                    inspector = inspect(engine.sync_engine)
                    tables = inspector.get_table_names()
                    click.echo(f"  Tables: {len(tables)}")
                    if tables:
                        click.echo(f"    {', '.join(tables)}")
            except Exception as e:
                click.echo(f"  Tables: Error ({e})")
        
        asyncio.run(_show_info())
        
    except Exception as e:
        logger.error(f"Failed to show database info: {e}", exc_info=True)
        click.echo(f"✗ Error: {str(e)}", err=True)
        sys.exit(1)

