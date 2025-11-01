"""
Main bot entry point.

Provides graceful shutdown handling for the Telegram bot.
"""

import asyncio
import signal
import sys
from typing import Any

from aiogram import Bot, Dispatcher

from Systems.core.bot.dispatcher import create_bot, create_dispatcher
from Systems.core.database import close_db, init_db
from Systems.core.logger import get_logger, setup_logger
from Systems.core.utils.config import get_config

logger = get_logger(__name__)


async def shutdown_handler(
    bot: Bot,
    dp: Dispatcher,
    shutdown_event: asyncio.Event,
) -> None:
    """
    Handle graceful shutdown.
    
    Args:
        bot: Bot instance
        dp: Dispatcher instance
        shutdown_event: Shutdown event
    """
    logger.info("🛑 Shutting down...")
    
    try:
        # Stop polling if it's running
        try:
            await dp.stop_polling()
        except RuntimeError as e:
            if "Polling is not started" in str(e):
                pass  # Already stopped, no need to log
            else:
                raise
        
        # Close bot session
        try:
            await bot.session.close()
        except Exception:
            pass
        
        # Close database connections
        await close_db()
        
        logger.info("✅ Shutdown complete")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}", exc_info=True)
    finally:
        shutdown_event.set()


async def main() -> None:
    """
    Main bot entry point.
    
    Loads configuration, initializes database, creates bot and dispatcher,
    and starts polling with graceful shutdown.
    
    Example:
        ```python
        # Run bot
        asyncio.run(main())
        
        # Or use CLI
        sdb service start
        ```
    """
    bot: Bot | None = None
    dp: Dispatcher | None = None
    shutdown_event = asyncio.Event()
    
    try:
        # Setup logging
        config = get_config()
        setup_logger(
            log_level=config.log_level,
            module_name="bot",
        )
        
        logger.info("🚀 Starting SwiftDevBot...")
        
        # Initialize database
        await init_db()
        logger.debug("Database initialized")
        
        # Create bot and dispatcher
        bot = create_bot()
        dp = create_dispatcher()
        
        # Setup graceful shutdown
        shutdown_event = asyncio.Event()
        polling_task_ref: list[asyncio.Task] = []  # Use list to store task reference
        
        def signal_handler(sig: int, frame: Any) -> None:
            """Handle shutdown signals (SIGINT, SIGTERM)."""
            logger.info(f"Received signal {sig} (Ctrl+C), initiating graceful shutdown...")
            shutdown_event.set()
            # Cancel polling task if exists
            if polling_task_ref:
                task = polling_task_ref[0]
                if task and not task.done():
                    task.cancel()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Start polling
        logger.info(f"🤖 Bot @{config.bot_username} is running. Press Ctrl+C to stop.")
        
        try:
            # Start polling in a task
            polling_task = asyncio.create_task(
                dp.start_polling(
                    bot,
                    allowed_updates=dp.resolve_used_update_types(),
                )
            )
            polling_task_ref.append(polling_task)
            
            # Wait for shutdown signal or polling to complete
            try:
                # Wait for either shutdown event or polling task to complete
                done, pending = await asyncio.wait(
                    {asyncio.create_task(shutdown_event.wait()), polling_task},
                    return_when=asyncio.FIRST_COMPLETED,
                )
                
                # Cancel pending tasks
                for task in pending:
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
                
            except asyncio.CancelledError:
                pass
            
            # Stop polling gracefully if still running
            if not polling_task.done():
                logger.info("Stopping polling...")
                try:
                    await dp.stop_polling()
                except RuntimeError as e:
                    if "Polling is not started" in str(e):
                        logger.debug("Polling was not started, skipping stop")
                    else:
                        raise
            
            # Wait for polling task to finish
            try:
                await asyncio.wait_for(polling_task, timeout=5.0)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                logger.warning("Polling task did not stop in time")
            
        except KeyboardInterrupt:
            logger.info("⏹ Interrupted by user")
        except asyncio.CancelledError:
            pass  # Silent cancellation
        finally:
            # Ensure cleanup happens
            await shutdown_handler(bot, dp, shutdown_event)
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        if bot and dp:
            await shutdown_handler(bot, dp, shutdown_event)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

