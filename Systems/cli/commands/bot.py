"""
CLI commands for bot management.
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional

import click

from Systems.core.database import get_session_factory
from Systems.core.logger import get_logger
from Systems.core.modules.loader import ModuleLoader
from Systems.core.modules.manager import ModuleManager
from Systems.core.utils.config import get_config
from sqlalchemy import text

logger = get_logger(__name__)


@click.group(name="bot")
def bot_group() -> None:
    """Bot management commands."""
    pass


@bot_group.command("start")
def start() -> None:
    """
    Start the bot service.
    
    Example:
        sdb bot start
    """
    try:
        click.echo("Starting bot service...")
        logger.info("Starting bot service via CLI")
        
        # Lazy import to avoid circular dependencies
        try:
            from Systems.core.bot.main import main as run_bot
            
            # Run bot in async context
            try:
                asyncio.run(run_bot())
            except KeyboardInterrupt:
                click.echo("\nStopped by user")
                logger.info("Bot service stopped by user")
        except ImportError as e:
            logger.error(f"Failed to import bot main: {e}")
            click.echo(f"Error: Failed to start bot service: {e}", err=True)
            sys.exit(1)
        
    except Exception as e:
        logger.error(f"Failed to start service: {e}", exc_info=True)
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


@bot_group.command("stop")
def stop() -> None:
    """
    Stop the bot service.
    
    Example:
        sdb bot stop
    """
    try:
        import psutil
        import os
        
        click.echo("Stopping bot service...")
        
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
                click.echo("✓ Bot service stopped gracefully")
                logger.info(f"Bot process {bot_process.pid} stopped")
            except psutil.TimeoutExpired:
                # Force kill if didn't stop gracefully
                bot_process.kill()
                click.echo("⚠ Bot service force stopped")
                logger.warning(f"Bot process {bot_process.pid} force killed")
            except Exception as e:
                click.echo(f"✗ Error stopping bot: {e}", err=True)
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
                            click.echo("✓ Bot service stopped")
                            return
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                    continue
            
            click.echo("⚠ Bot service not running")
            logger.info("Bot stop requested but no running process found")
        
    except ImportError:
        click.echo("✗ Error: psutil not installed. Install with: pip install psutil", err=True)
        click.echo("  Alternative: Use Ctrl+C in the terminal where bot is running", err=True)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to stop service: {e}", exc_info=True)
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


@bot_group.command("restart")
def restart() -> None:
    """
    Restart the bot service.
    
    Example:
        sdb bot restart
    """
    try:
        # Stop first
        stop()
        
        # Wait a moment
        import time
        time.sleep(1)
        
        # Start
        click.echo("Restarting bot service...")
        start()
        
    except Exception as e:
        logger.error(f"Failed to restart service: {e}", exc_info=True)
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


@bot_group.command("status")
def status() -> None:
    """
    Show bot service status.
    
    Example:
        sdb bot status
    """
    try:
        import psutil
        import os
        
        click.echo("Bot Service Status:")
        click.echo("")
        
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
                        
                        click.echo(f"  Bot: ✓ Running")
                        click.echo(f"    PID: {bot_pid}")
                        click.echo(f"    Status: {status_info}")
                        click.echo(f"    Uptime: {uptime_str}")
                        break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        if not bot_running:
            click.echo("  Bot: ✗ Not running")
        
        # Check web panel (if possible)
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = ' '.join(proc.info.get('cmdline', []))
                    if 'uvicorn' in cmdline.lower() and 'Systems.web.app' in cmdline:
                        click.echo(f"  Web Panel: ✓ Running (PID: {proc.info['pid']})")
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            else:
                click.echo("  Web Panel: ✗ Not running")
        except Exception:
            click.echo("  Web Panel: ? Unknown")
        
    except ImportError:
        click.echo("  Bot: ? Unknown (psutil not installed)")
        click.echo("  Install psutil for detailed status: pip install psutil")
        logger.debug("Service status checked (psutil not available)")
    except Exception as e:
        logger.error(f"Failed to get service status: {e}", exc_info=True)
        click.echo(f"✗ Error: {str(e)}", err=True)
        sys.exit(1)


@bot_group.command("stats")
def stats() -> None:
    """
    Show bot statistics.
    
    Example:
        sdb bot stats
    """
    try:
        async def _show_stats() -> None:
            config = get_config()
            
            click.echo("Bot Statistics:")
            click.echo("")
            click.echo(f"  Bot Username: @{config.bot_username}")
            click.echo(f"  Super Admin ID: {config.super_admin_id}")
            
            # Database stats
            try:
                async with get_session_factory()() as session:
                    # User count
                    try:
                        result = await session.execute(text("SELECT COUNT(*) FROM users"))
                        user_count = result.scalar()
                        click.echo(f"  Total Users: {user_count}")
                        
                        # Active users
                        result = await session.execute(
                            text("SELECT COUNT(*) FROM users WHERE is_active = true")
                        )
                        active_users = result.scalar()
                        click.echo(f"  Active Users: {active_users}")
                    except Exception:
                        click.echo("  Total Users: N/A (database not initialized)")
                        click.echo("  Active Users: N/A")
                    
                    # Audit log entries
                    try:
                        result = await session.execute(text("SELECT COUNT(*) FROM audit_logs"))
                        audit_count = result.scalar()
                        click.echo(f"  Audit Log Entries: {audit_count}")
                    except Exception:
                        click.echo("  Audit Log Entries: N/A")
            except Exception as e:
                click.echo(f"  Database: Error ({e})")
                
                # Modules count
                modules_dir = Path("Modules")
                if modules_dir.exists():
                    modules = [d.name for d in modules_dir.iterdir() if d.is_dir() and not d.name.startswith("_")]
                    click.echo(f"  Installed Modules: {len(modules)}")
                    
                    # Loaded modules
                    try:
                        loader = ModuleLoader(modules_dir)
                        loaded = loader.get_loaded_modules()
                        enabled_count = sum(1 for m in loaded.values() if m and m.enabled)
                        click.echo(f"  Enabled Modules: {enabled_count}")
                    except Exception:
                        pass
                
                # Audit log entries
                try:
                    result = await session.execute(text("SELECT COUNT(*) FROM audit_logs"))
                    audit_count = result.scalar()
                    click.echo(f"  Audit Log Entries: {audit_count}")
                except Exception:
                    pass
            
            click.echo("")
            click.echo("✓ Statistics retrieved")
        
        asyncio.run(_show_stats())
        
    except Exception as e:
        logger.error(f"Failed to get bot stats: {e}", exc_info=True)
        click.echo(f"✗ Error: {str(e)}", err=True)
        sys.exit(1)


@bot_group.command("version")
def version() -> None:
    """
    Show bot version and information.
    
    Example:
        sdb bot version
    """
    try:
        config = get_config()
        
        click.echo("SwiftDevBot Information:")
        click.echo("")
        click.echo(f"  Version: 1.0.0")
        click.echo(f"  Bot Username: @{config.bot_username}")
        click.echo(f"  Database: {config.db_type}")
        click.echo(f"  Redis: {config.redis_host}:{config.redis_port}")
        click.echo(f"  Log Level: {config.log_level}")
        click.echo("")
        click.echo("✓ Information retrieved")
        
    except Exception as e:
        logger.error(f"Failed to get version: {e}", exc_info=True)
        click.echo(f"✗ Error: {str(e)}", err=True)
        sys.exit(1)


@bot_group.command("test")
def test() -> None:
    """
    Test bot configuration and connectivity.
    
    Example:
        sdb bot test
    """
    try:
        async def _test_bot() -> None:
            config = get_config()
            issues = []
            
            click.echo("Testing bot configuration...")
            click.echo("")
            
            # Test database
            try:
                async with get_session_factory()() as session:
                    await session.execute(text("SELECT 1"))
                click.echo("✓ Database: OK")
            except Exception as e:
                click.echo(f"✗ Database: FAILED ({e})")
                issues.append("Database connection failed")
            
            # Test Redis (if configured)
            try:
                import redis
                r = redis.Redis(host=config.redis_host, port=config.redis_port, db=config.redis_db)
                r.ping()
                click.echo("✓ Redis: OK")
            except Exception as e:
                click.echo(f"✗ Redis: FAILED ({e})")
                issues.append("Redis connection failed")
            
            # Test bot token (if available)
            if config.bot_token and config.bot_token != "test_token":
                try:
                    from aiogram import Bot
                    bot = Bot(token=config.bot_token)
                    bot_info = await bot.get_me()
                    await bot.session.close()
                    click.echo(f"✓ Bot Token: OK (@{bot_info.username})")
                except Exception as e:
                    click.echo(f"✗ Bot Token: FAILED ({e})")
                    issues.append("Bot token invalid")
            
            # Check modules
            modules_dir = Path("Modules")
            if modules_dir.exists():
                modules = [d.name for d in modules_dir.iterdir() if d.is_dir() and not d.name.startswith("_")]
                click.echo(f"✓ Modules: {len(modules)} installed")
            
            click.echo("")
            
            if issues:
                click.echo(f"✗ Found {len(issues)} issues:")
                for issue in issues:
                    click.echo(f"  - {issue}")
                sys.exit(1)
            else:
                click.echo("✓ All tests passed!")
        
        asyncio.run(_test_bot())
        
    except Exception as e:
        logger.error(f"Bot test failed: {e}", exc_info=True)
        click.echo(f"✗ Error: {str(e)}", err=True)
        sys.exit(1)


@bot_group.command("clean")
@click.option("--logs", is_flag=True, help="Clean old log files")
@click.option("--cache", is_flag=True, help="Clean cache files")
@click.option("--all", "clean_all", is_flag=True, help="Clean everything")
def clean(logs: bool, cache: bool, clean_all: bool) -> None:
    """
    Clean temporary files and old data.
    
    Options:
        --logs: Clean old log files
        --cache: Clean cache files (__pycache__)
        --all: Clean everything
    
    Example:
        sdb bot clean --logs
        sdb bot clean --all
    """
    try:
        from pathlib import Path
        import shutil
        
        if clean_all:
            logs = True
            cache = True
        
        if not (logs or cache):
            click.echo("No cleanup options specified. Use --logs, --cache, or --all")
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
            click.echo(f"✓ Cleaned: {', '.join(cleaned)}")
        else:
            click.echo("✓ Nothing to clean")
        
    except Exception as e:
        logger.error(f"Clean failed: {e}", exc_info=True)
        click.echo(f"✗ Error: {str(e)}", err=True)
        sys.exit(1)

