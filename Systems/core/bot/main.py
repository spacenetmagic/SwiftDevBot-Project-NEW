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
    logger.info("Initiating graceful shutdown...")
    
    try:
        # Stop polling
        await dp.stop_polling()
        logger.info("Bot polling stopped")
        
        # Close bot session
        await bot.session.close()
        logger.info("Bot session closed")
        
        # Close database connections
        await close_db()
        logger.info("Database connections closed")
        
        logger.info("Graceful shutdown complete")
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
        
        logger.info("=" * 50)
        logger.info("Starting SwiftDevBot...")
        logger.info("=" * 50)
        
        # Initialize database
        logger.info("Initializing database...")
        await init_db()
        logger.info("Database initialized")
        
        # Create bot and dispatcher
        logger.info("Creating bot and dispatcher...")
        bot = create_bot()
        dp = create_dispatcher()
        
        # Setup graceful shutdown
        shutdown_event = asyncio.Event()
        
        def signal_handler(sig: int, frame: Any) -> None:
            """Handle shutdown signals (SIGINT, SIGTERM)."""
            logger.info(f"Received signal {sig}, initiating graceful shutdown...")
            if not shutdown_event.is_set():
                asyncio.create_task(shutdown_handler(bot, dp, shutdown_event))
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Start polling
        logger.info("Starting bot polling...")
        logger.info(f"Bot username: @{config.bot_username}")
        logger.info("Bot is running. Press Ctrl+C to stop.")
        
        # Start polling in background
        polling_task = asyncio.create_task(
            dp.start_polling(
                bot,
                allowed_updates=dp.resolve_used_update_types(),
            )
        )
        
        # Wait for shutdown signal
        await shutdown_event.wait()
        
        # Wait for polling to stop
        try:
            await asyncio.wait_for(polling_task, timeout=10.0)
        except asyncio.TimeoutError:
            logger.warning("Polling task did not stop in time, forcing shutdown")
            polling_task.cancel()
        
        logger.info("Bot stopped successfully")
        
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        if bot and dp:
            await shutdown_handler(bot, dp, shutdown_event)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        if bot and dp:
            await shutdown_handler(bot, dp, shutdown_event)
        sys.exit(1)
    finally:
        logger.info("Bot shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())

