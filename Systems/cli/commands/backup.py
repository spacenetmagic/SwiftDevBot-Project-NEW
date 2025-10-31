"""
CLI commands for backup management.
"""

import shutil
import tarfile
from datetime import datetime
from pathlib import Path

import click

from typing import Optional

from Systems.core.database import get_session_factory
from Systems.core.logger import get_logger
from Systems.core.utils.config import Config

logger = get_logger(__name__)


@click.group(name="backup")
def backup_group() -> None:
    """Backup management commands."""
    pass


@backup_group.command("create")
@click.option("--name", help="Backup name (defaults to timestamp)")
@click.option("--include-db", is_flag=True, help="Include database")
@click.option("--include-modules", is_flag=True, help="Include modules")
@click.option("--include-logs", is_flag=True, help="Include logs")
def create(name: Optional[str], include_db: bool, include_modules: bool, include_logs: bool) -> None:
    """
    Create a backup.
    
    Args:
        name: Backup name (optional)
        include_db: Include database files
        include_modules: Include modules directory
        include_logs: Include log files
    
    Example:
        sdb backup create
        sdb backup create --include-db --include-modules
        sdb backup create --name my_backup
    """
    try:
        backup_dir = Path("Backups")
        backup_dir.mkdir(exist_ok=True)
        
        # Generate backup name
        if not name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            name = f"backup_{timestamp}"
        
        backup_path = backup_dir / f"{name}.tar.gz"
        
        if backup_path.exists():
            if not click.confirm(f"Backup {name} already exists. Overwrite?"):
                click.echo("Cancelled")
                return
        
        click.echo(f"Creating backup: {name}")
        
        # Default: include everything
        if not (include_db or include_modules or include_logs):
            include_db = True
            include_modules = True
            include_logs = True
        
        # Create tar archive
        with tarfile.open(backup_path, "w:gz") as tar:
            config = Config()
            
            # Database
            if include_db:
                if config.db_type == "sqlite":
                    db_path = Path(config.db_path)
                    if db_path.exists():
                        tar.add(db_path, arcname=f"database/{db_path.name}")
                        logger.debug(f"Added database to backup: {db_path}")
            
            # Modules
            if include_modules:
                modules_dir = Path("Modules")
                if modules_dir.exists():
                    tar.add(modules_dir, arcname="Modules")
                    logger.debug(f"Added modules to backup: {modules_dir}")
            
            # Logs
            if include_logs:
                logs_dir = Path("Logs")
                if logs_dir.exists():
                    tar.add(logs_dir, arcname="Logs")
                    logger.debug(f"Added logs to backup: {logs_dir}")
            
            # Config file
            config_file = Path(".env")
            if config_file.exists():
                tar.add(config_file, arcname=".env")
                logger.debug(f"Added config to backup: {config_file}")
        
        size_mb = backup_path.stat().st_size / (1024 * 1024)
        click.echo(f"✓ Backup created: {backup_path} ({size_mb:.2f} MB)")
        logger.info(f"Backup created: {name}")
        
    except Exception as e:
        logger.error(f"Failed to create backup: {e}", exc_info=True)
        click.echo(f"Error: {str(e)}", err=True)
        click.get_current_context().exit(1)


@backup_group.command("restore")
@click.argument("name")
@click.option("--force", is_flag=True, help="Force restore without confirmation")
def restore(name: str, force: bool) -> None:
    """
    Restore a backup.
    
    Args:
        name: Backup name (without .tar.gz extension)
        force: Force restore without confirmation
    
    Example:
        sdb backup restore backup_20240101_120000
        sdb backup restore my_backup --force
    """
    try:
        backup_dir = Path("Backups")
        backup_path = backup_dir / f"{name}.tar.gz"
        
        if not backup_path.exists():
            click.echo(f"Error: Backup {name} not found", err=True)
            click.get_current_context().exit(1)
        
        if not force:
            if not click.confirm(f"Are you sure you want to restore backup {name}? This will overwrite existing files."):
                click.echo("Cancelled")
                return
        
        click.echo(f"Restoring backup: {name}")
        
        # Extract backup
        with tarfile.open(backup_path, "r:gz") as tar:
            tar.extractall(path=".")
        
        click.echo(f"✓ Backup {name} restored successfully")
        logger.info(f"Backup restored: {name}")
        
    except Exception as e:
        logger.error(f"Failed to restore backup: {e}", exc_info=True)
        click.echo(f"Error: {str(e)}", err=True)
        click.get_current_context().exit(1)


@backup_group.command("list")
def list_backups() -> None:
    """
    List all backups.
    
    Example:
        sdb backup list
    """
    try:
        backup_dir = Path("Backups")
        
        if not backup_dir.exists():
            click.echo("No backups directory found")
            return
        
        backups = sorted(backup_dir.glob("*.tar.gz"), key=lambda p: p.stat().st_mtime, reverse=True)
        
        if not backups:
            click.echo("No backups found")
            return
        
        click.echo(f"Backups ({len(backups)}):")
        click.echo("")
        click.echo(f"{'Name':<30} {'Size':<10} {'Date':<20}")
        click.echo("-" * 70)
        
        for backup in backups:
            name = backup.stem
            size_mb = backup.stat().st_size / (1024 * 1024)
            date = datetime.fromtimestamp(backup.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            click.echo(f"{name:<30} {size_mb:>7.2f} MB  {date:<20}")
        
    except Exception as e:
        logger.error(f"Failed to list backups: {e}", exc_info=True)
        click.echo(f"Error: {str(e)}", err=True)
        click.get_current_context().exit(1)

