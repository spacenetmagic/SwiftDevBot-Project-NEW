"""
CLI commands for bot management with Typer + Rich.
"""

import asyncio
import sys
from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

from Systems.core.database import get_session_factory
from Systems.core.logger import get_logger
from Systems.core.modules.loader import ModuleLoader
from Systems.core.modules.manager import ModuleManager
from Systems.core.utils.config import get_config
from sqlalchemy import text

logger = get_logger(__name__)

# Create Typer app
app = typer.Typer(
    name="bot",
    help="Bot management commands",
    rich_markup_mode="rich",
)

# Create console for Rich output
console = Console()


@app.command("start", help="Start the bot service")
def start() -> None:
    """Start the bot service."""
    try:
        console.print("[bold green]Starting bot service...[/bold green]")
        logger.info("Starting bot service via CLI")
        
        # Lazy import to avoid circular dependencies
        try:
            from Systems.core.bot.main import main as run_bot
            
            # Run bot in async context
            try:
                asyncio.run(run_bot())
            except KeyboardInterrupt:
                console.print("\n[yellow]Stopped by user[/yellow]")
                logger.info("Bot service stopped by user")
        except ImportError as e:
            logger.error(f"Failed to import bot main: {e}")
            console.print(f"[red]Error:[/red] Failed to start bot service: {e}")
            sys.exit(1)
        
    except Exception as e:
        logger.error(f"Failed to start service: {e}", exc_info=True)
        console.print(f"[red]Error:[/red] {str(e)}")
        sys.exit(1)


@app.command("stop", help="Stop the bot service")
def stop() -> None:
    """Stop the bot service."""
    try:
        import psutil
        import os
        
        console.print("[yellow]Stopping bot service...[/yellow]")
        
        # Find bot process
        current_pid = os.getpid()
        bot_process = None
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info.get('cmdline', [])
                # Check if it's a Python process running bot
                if any('Systems.core.bot.main' in str(cmd) or 'sdb bot start' in str(cmd) 
                       for cmd in cmdline):
                    if proc.info['pid'] != current_pid:
                        bot_process = proc
                        break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        if bot_process:
            try:
                bot_process.terminate()
                # Wait for graceful shutdown (5 seconds)
                bot_process.wait(timeout=5)
                console.print("[green]✓[/green] Bot service stopped gracefully")
                logger.info(f"Bot process {bot_process.pid} stopped")
            except psutil.TimeoutExpired:
                # Force kill if didn't stop gracefully
                bot_process.kill()
                console.print("[yellow]⚠[/yellow] Bot service force stopped")
                logger.warning(f"Bot process {bot_process.pid} force killed")
            except Exception as e:
                console.print(f"[red]✗[/red] Error stopping bot: {e}")
                sys.exit(1)
        else:
            # Try to find by process name pattern
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = ' '.join(proc.info.get('cmdline', []))
                    if 'python' in cmdline.lower() and 'bot' in cmdline.lower():
                        if proc.info['pid'] != current_pid:
                            proc.terminate()
                            proc.wait(timeout=3)
                            console.print("[green]✓[/green] Bot service stopped")
                            return
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                    continue
            
            console.print("[yellow]⚠[/yellow] Bot service not running")
            logger.info("Bot stop requested but no running process found")
        
    except ImportError:
        console.print("[red]✗[/red] Error: psutil not installed. Install with: [cyan]pip install psutil[/cyan]")
        console.print("  Alternative: Use Ctrl+C in the terminal where bot is running")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to stop service: {e}", exc_info=True)
        console.print(f"[red]Error:[/red] {str(e)}")
        sys.exit(1)


@app.command("restart", help="Restart the bot service")
def restart() -> None:
    """Restart the bot service."""
    try:
        # Stop first
        stop()
        
        # Wait a moment
        import time
        time.sleep(1)
        
        # Start
        console.print("[bold green]Restarting bot service...[/bold green]")
        start()
        
    except Exception as e:
        logger.error(f"Failed to restart service: {e}", exc_info=True)
        console.print(f"[red]Error:[/red] {str(e)}")
        sys.exit(1)


@app.command("status", help="Show bot service status")
def status() -> None:
    """Show bot service status."""
    try:
        import psutil
        import os
        
        table = Table(title="Bot Service Status", box=box.ROUNDED)
        table.add_column("Service", style="cyan")
        table.add_column("Status", justify="center")
        table.add_column("Details", style="dim")
        
        current_pid = os.getpid()
        bot_running = False
        bot_pid = None
        
        # Check for bot process
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'status', 'create_time']):
            try:
                cmdline = proc.info.get('cmdline', [])
                if any('Systems.core.bot.main' in str(cmd) or 'sdb bot start' in str(cmd) 
                       for cmd in cmdline):
                    if proc.info['pid'] != current_pid:
                        bot_running = True
                        bot_pid = proc.info['pid']
                        status_info = proc.info.get('status', 'unknown')
                        create_time = proc.info.get('create_time', 0)
                        
                        if create_time:
                            from datetime import datetime
                            uptime = datetime.now() - datetime.fromtimestamp(create_time)
                            uptime_str = str(uptime).split('.')[0]  # Remove microseconds
                        else:
                            uptime_str = "unknown"
                        
                        table.add_row(
                            "Bot",
                            "[green]✓ Running[/green]",
                            f"PID: {bot_pid} | Status: {status_info} | Uptime: {uptime_str}"
                        )
                        break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        if not bot_running:
            table.add_row("Bot", "[red]✗ Not running[/red]", "")
        
        # Check web panel (if possible)
        try:
            web_running = False
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = ' '.join(proc.info.get('cmdline', []))
                    if 'uvicorn' in cmdline.lower() and 'Systems.web.app' in cmdline:
                        web_running = True
                        table.add_row(
                            "Web Panel",
                            "[green]✓ Running[/green]",
                            f"PID: {proc.info['pid']}"
                        )
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            if not web_running:
                table.add_row("Web Panel", "[red]✗ Not running[/red]", "")
        except Exception:
            table.add_row("Web Panel", "[yellow]? Unknown[/yellow]", "")
        
        console.print(table)
        
    except ImportError:
        console.print("[yellow]⚠[/yellow] psutil not installed. Install with: [cyan]pip install psutil[/cyan]")
        logger.debug("Service status checked (psutil not available)")
    except Exception as e:
        logger.error(f"Failed to get service status: {e}", exc_info=True)
        console.print(f"[red]Error:[/red] {str(e)}")
        sys.exit(1)


@app.command("stats", help="Show bot statistics")
def stats() -> None:
    """Show bot statistics."""
    try:
        async def _show_stats() -> None:
            config = get_config()
            
            table = Table(title="Bot Statistics", box=box.ROUNDED)
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            
            table.add_row("Bot Username", f"@{config.bot_username}")
            table.add_row("Super Admin ID", str(config.super_admin_id))
            
            # Database stats
            try:
                async with get_session_factory()() as session:
                    # User count
                    try:
                        result = await session.execute(text("SELECT COUNT(*) FROM users"))
                        user_count = result.scalar()
                        table.add_row("Total Users", str(user_count))
                        
                        # Active users
                        result = await session.execute(
                            text("SELECT COUNT(*) FROM users WHERE is_active = true")
                        )
                        active_users = result.scalar()
                        table.add_row("Active Users", str(active_users))
                    except Exception:
                        table.add_row("Total Users", "[yellow]N/A (database not initialized)[/yellow]")
                        table.add_row("Active Users", "[yellow]N/A[/yellow]")
                    
                    # Audit log entries
                    try:
                        result = await session.execute(text("SELECT COUNT(*) FROM audit_logs"))
                        audit_count = result.scalar()
                        table.add_row("Audit Log Entries", str(audit_count))
                    except Exception:
                        table.add_row("Audit Log Entries", "[yellow]N/A[/yellow]")
            except Exception as e:
                table.add_row("Database", f"[red]Error ({e})[/red]")
            
            # Modules count
            modules_dir = Path("Modules")
            if modules_dir.exists():
                modules = [d.name for d in modules_dir.iterdir() if d.is_dir() and not d.name.startswith("_")]
                table.add_row("Installed Modules", str(len(modules)))
                
                # Loaded modules
                try:
                    loader = ModuleLoader(modules_dir)
                    loaded = loader.get_loaded_modules()
                    enabled_count = sum(1 for m in loaded.values() if m and m.enabled)
                    table.add_row("Enabled Modules", str(enabled_count))
                except Exception:
                    pass
            
            console.print(table)
            console.print("[green]✓ Statistics retrieved[/green]")
        
        asyncio.run(_show_stats())
        
    except Exception as e:
        logger.error(f"Failed to get bot stats: {e}", exc_info=True)
        console.print(f"[red]Error:[/red] {str(e)}")
        sys.exit(1)


@app.command("version", help="Show bot version and information")
def version() -> None:
    """Show bot version and information."""
    try:
        config = get_config()
        
        table = Table(title="SwiftDevBot Information", box=box.ROUNDED)
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Version", "1.0.0")
        table.add_row("Bot Username", f"@{config.bot_username}")
        table.add_row("Database", config.db_type)
        
        if config.use_redis:
            table.add_row("Redis", f"{config.redis_host}:{config.redis_port} [dim](enabled)[/dim]")
        else:
            table.add_row("Redis", "[dim]disabled (using MemoryStorage)[/dim]")
        
        table.add_row("Log Level", config.log_level)
        
        console.print(table)
        console.print("[green]✓ Information retrieved[/green]")
        
    except Exception as e:
        logger.error(f"Failed to get version: {e}", exc_info=True)
        console.print(f"[red]Error:[/red] {str(e)}")
        sys.exit(1)


@app.command("test", help="Test bot configuration and connectivity")
def test() -> None:
    """Test bot configuration and connectivity."""
    try:
        async def _test_bot() -> None:
            config = get_config()
            issues = []
            
            console.print("[bold]Testing bot configuration...[/bold]")
            console.print()
            
            # Test database
            try:
                async with get_session_factory()() as session:
                    await session.execute(text("SELECT 1"))
                console.print("[green]✓[/green] Database: OK")
            except Exception as e:
                console.print(f"[red]✗[/red] Database: FAILED ({e})")
                issues.append("Database connection failed")
            
            # Test Redis (if enabled)
            if config.use_redis:
                try:
                    import redis
                    r = redis.Redis(host=config.redis_host, port=config.redis_port, db=0)
                    r.ping()
                    console.print("[green]✓[/green] Redis: OK")
                except ImportError:
                    console.print("[yellow]⚠[/yellow] Redis: Package not installed ([cyan]pip install redis[/cyan])")
                    console.print("   [dim]Using MemoryStorage instead[/dim]")
                except Exception as e:
                    console.print(f"[yellow]⚠[/yellow] Redis: FAILED ({e})")
                    console.print("   [dim]Using MemoryStorage instead[/dim]")
                    console.print("   [dim]Tip: Set USE_REDIS=false in .env to disable Redis checks[/dim]")
            else:
                console.print("[dim]ℹ[/dim] Redis: Disabled (using MemoryStorage)")
            
            # Test bot token (if available)
            if config.bot_token and config.bot_token != "test_token":
                try:
                    from aiogram import Bot
                    bot = Bot(token=config.bot_token)
                    bot_info = await bot.get_me()
                    await bot.session.close()
                    console.print(f"[green]✓[/green] Bot Token: OK (@{bot_info.username})")
                except Exception as e:
                    console.print(f"[red]✗[/red] Bot Token: FAILED ({e})")
                    issues.append("Bot token invalid")
            
            # Check modules
            modules_dir = Path("Modules")
            if modules_dir.exists():
                modules = [d.name for d in modules_dir.iterdir() if d.is_dir() and not d.name.startswith("_")]
                console.print(f"[green]✓[/green] Modules: {len(modules)} installed")
            
            console.print()
            
            if issues:
                console.print(f"[red]✗ Found {len(issues)} issues:[/red]")
                for issue in issues:
                    console.print(f"  [red]-[/red] {issue}")
                sys.exit(1)
            else:
                console.print("[green]✓ All tests passed![/green]")
        
        asyncio.run(_test_bot())
        
    except Exception as e:
        logger.error(f"Bot test failed: {e}", exc_info=True)
        console.print(f"[red]Error:[/red] {str(e)}")
        sys.exit(1)


@app.command("clean", help="Clean temporary files and old data")
def clean(
    logs: Annotated[bool, typer.Option("--logs", help="Clean old log files")] = False,
    cache: Annotated[bool, typer.Option("--cache", help="Clean cache files")] = False,
    all_files: Annotated[bool, typer.Option("--all", help="Clean everything")] = False,
) -> None:
    """Clean temporary files and old data."""
    try:
        from pathlib import Path
        import shutil
        
        if all_files:
            logs = True
            cache = True
        
        if not (logs or cache):
            console.print("[yellow]⚠[/yellow] No cleanup options specified. Use [cyan]--logs[/cyan], [cyan]--cache[/cyan], or [cyan]--all[/cyan]")
            return
        
        cleaned = []
        
        # Clean logs
        if logs:
            logs_dir = Path("Data/logs")
            if logs_dir.exists():
                # Remove log files older than 30 days
                import time
                cutoff = time.time() - (30 * 24 * 60 * 60)
                
                count = 0
                for log_file in logs_dir.glob("*.log"):
                    if log_file.stat().st_mtime < cutoff:
                        log_file.unlink()
                        count += 1
                
                cleaned.append(f"{count} old log files")
        
        # Clean cache
        if cache:
            count = 0
            for cache_dir in Path(".").rglob("__pycache__"):
                shutil.rmtree(cache_dir)
                count += 1
            cleaned.append(f"{count} cache directories")
        
        if cleaned:
            console.print(f"[green]✓[/green] Cleaned: {', '.join(cleaned)}")
        else:
            console.print("[green]✓[/green] Nothing to clean")
        
    except Exception as e:
        logger.error(f"Clean failed: {e}", exc_info=True)
        console.print(f"[red]Error:[/red] {str(e)}")
        sys.exit(1)
