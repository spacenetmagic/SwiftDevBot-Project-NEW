"""
CLI commands for development tools.
"""

import subprocess
import sys
from pathlib import Path
from typing import Optional

import click

from Systems.core.logger import get_logger

logger = get_logger(__name__)


@click.group(name="dev")
def dev_group() -> None:
    """Development tools commands."""
    pass


@dev_group.command("watch")
def watch() -> None:
    """
    Watch for changes and auto-reload modules (development mode).
    
    Example:
        sdb dev watch
    """
    try:
        # This is the same as 'module watch'
        # Delegate to module watch command
        from Systems.cli.commands.module import watch as module_watch
        
        module_watch()
        
    except Exception as e:
        logger.error(f"Failed to watch for changes: {e}", exc_info=True)
        click.echo(f"Error: {str(e)}", err=True)
        click.get_current_context().exit(1)


@dev_group.command("clean-logs")
@click.option("--confirm", is_flag=True, help="Skip confirmation prompt")
def clean_logs(confirm: bool) -> None:
    """
    Clean old log files (keeps only app.log and app_errors.log).
    
    Removes all per-module log files created by old logging system.
    
    Example:
        sdb dev clean-logs
        sdb dev clean-logs --confirm
    """
    from pathlib import Path
    
    log_dir = Path("Data/logs")
    
    if not log_dir.exists():
        click.echo("Log directory not found")
        return
    
    # Find all old log files (everything except category-based logs)
    protected_logs = {
        "app.log", "app_errors.log",
        "bot.log", "bot_errors.log",
        "web.log", "web_errors.log",
        "core.log", "core_errors.log",
        "modules.log", "modules_errors.log"
    }
    
    old_logs = [
        f for f in log_dir.glob("*.log")
        if f.name not in protected_logs
    ]
    
    if not old_logs:
        click.echo("No old log files to clean")
        return
    
    if not confirm:
        click.echo(f"Found {len(old_logs)} old log files to remove:")
        for log_file in old_logs[:10]:  # Show first 10
            click.echo(f"  - {log_file.name}")
        if len(old_logs) > 10:
            click.echo(f"  ... and {len(old_logs) - 10} more")
        if not click.confirm("Do you want to delete these files?"):
            click.echo("Cancelled")
            return
    
    # Delete old log files
    deleted = 0
    for log_file in old_logs:
        try:
            log_file.unlink()
            deleted += 1
        except Exception as e:
            logger.warning(f"Failed to delete {log_file.name}: {e}")
    
    click.echo(f"✓ Deleted {deleted} old log files")
    logger.info(f"Cleaned {deleted} old log files from {log_dir}")


@dev_group.command("logs")
@click.argument("service", required=False)
@click.option("--follow", "-f", is_flag=True, help="Follow log output")
@click.option("--lines", "-n", type=int, default=50, help="Number of lines to show")
def logs(service: Optional[str], follow: bool, lines: int) -> None:
    """
    Show service logs.
    
    Args:
        service: Service name (optional)
        follow: Follow log output
        lines: Number of lines to show
    
    Example:
        sdb dev logs
        sdb dev logs bot
        sdb dev logs --follow
        sdb dev logs --lines 100
    """
    try:
        log_dir = Path("Data/logs")
        
        if not log_dir.exists():
            click.echo("No logs directory found")
            return
        
        if service:
            # Support category-based logs: bot, web, core, modules
            if service == "errors":
                # Default to app_errors.log, but can specify category_errors
                log_file = log_dir / "app_errors.log"
            elif service.endswith("_errors"):
                # Support: bot_errors, web_errors, etc.
                category = service.replace("_errors", "")
                log_file = log_dir / f"{category}_errors.log"
            else:
                # Support: bot, web, core, modules, app
                log_file = log_dir / f"{service}.log"
        else:
            # Default to main app log (shows everything)
            log_file = log_dir / "app.log"
        
        if not log_file.exists():
            # Try to find any log file
            log_files = sorted(log_dir.glob("*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
            if not log_files:
                click.echo("No log files found")
                return
            log_file = log_files[0]
            
            if not log_file.exists():
                click.echo(f"Log file not found: {log_file}")
                return
        
        # Read log file
        if follow:
            # Use tail -f equivalent
            click.echo(f"Following logs: {log_file}")
            try:
                subprocess.run(["tail", "-f", str(log_file)], check=False)
            except FileNotFoundError:
                # Fallback: read file periodically
                click.echo("tail command not available, showing last lines:")
                with open(log_file, "r") as f:
                    for line in f:
                        click.echo(line, nl=False)
        else:
            # Read last N lines
            with open(log_file, "r") as f:
                all_lines = f.readlines()
                for line in all_lines[-lines:]:
                    click.echo(line, nl=False)
        
    except Exception as e:
        logger.error(f"Failed to show logs: {e}", exc_info=True)
        click.echo(f"Error: {str(e)}", err=True)
        click.get_current_context().exit(1)


@dev_group.command("shell")
def shell() -> None:
    """
    Open Python shell with app context.
    
    Example:
        sdb dev shell
    """
    try:
        import IPython
        
        # Create IPython shell with app context
        click.echo("Starting Python shell with SwiftDevBot context...")
        click.echo("")
        
        # Import common modules
        from Systems.core.utils.config import Config
        from Systems.core.database import get_session_factory
        
        # Prepare namespace
        namespace = {
            "Config": Config,
            "get_session_factory": get_session_factory,
            "config": Config(),
        }
        
        # Start IPython shell
        IPython.start_ipython(argv=[], user_ns=namespace)
        
    except ImportError:
        # Fallback to standard Python shell
        click.echo("IPython not available, using standard Python shell...")
        click.echo("")
        
        import code
        import readline
        import rlcompleter
        
        # Import common modules
        from Systems.core.utils.config import Config
        from Systems.core.database import get_session_factory
        
        # Prepare namespace
        namespace = {
            "Config": Config,
            "get_session_factory": get_session_factory,
            "config": Config(),
        }
        
        # Start interactive shell
        readline.parse_and_bind("tab: complete")
        shell = code.InteractiveConsole(namespace)
        shell.interact(banner="SwiftDevBot Python Shell\nType 'exit()' to quit")
        
    except Exception as e:
        logger.error(f"Failed to start shell: {e}", exc_info=True)
        click.echo(f"Error: {str(e)}", err=True)
        click.get_current_context().exit(1)

