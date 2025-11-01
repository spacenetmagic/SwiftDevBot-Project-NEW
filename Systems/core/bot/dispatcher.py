"""
Bot dispatcher setup.
"""

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.fsm.storage.memory import MemoryStorage

from Systems.core.bot.handlers.errors import register_error_handlers
from Systems.core.bot.handlers.start import router as start_router
from Systems.core.bot.middlewares.auth import AuthMiddleware
from Systems.core.bot.middlewares.logging import LoggingMiddleware
from Systems.core.bot.middlewares.rbac import RBACMiddleware
from Systems.core.logger import get_logger
from Systems.core.utils.config import get_config

logger = get_logger(__name__)


def create_dispatcher() -> Dispatcher:
    """
    Create and configure aiogram dispatcher.
    
    Sets up:
    - Middleware chain (Logging -> Auth -> RBAC)
    - Error handlers
    - FSM storage (Redis if available, otherwise Memory)
    - Routers
    
    Returns:
        Configured Dispatcher instance
        
    Example:
        ```python
        dp = create_dispatcher()
        bot = Bot(token=config.bot_token)
        await dp.start_polling(bot)
        ```
    """
    logger.info("Creating dispatcher...")
    
    config = get_config()
    
    # Setup FSM storage
    storage = None
    if config.use_redis:
        try:
            from redis.asyncio import Redis as AsyncRedis
            
            # Create Redis client with short timeouts to avoid long waits if Redis is unavailable
            redis_client = AsyncRedis(
                host=config.redis_host,
                port=config.redis_port,
                decode_responses=True,
                socket_connect_timeout=2,  # 2 seconds timeout for connection
                socket_timeout=2,  # 2 seconds timeout for operations
            )
            storage = RedisStorage(redis=redis_client)
            logger.info(f"✓ Redis FSM storage initialized: {config.redis_host}:{config.redis_port}")
        except ImportError:
            logger.warning("⚠ Redis package not installed (use: pip install redis), falling back to Memory storage")
            storage = MemoryStorage()
            logger.info("✓ Using Memory FSM storage (state will be lost on restart)")
        except (ConnectionError, OSError, TimeoutError) as e:
            logger.warning(f"⚠ Redis server not available ({type(e).__name__}: {e}), falling back to Memory storage")
            logger.info("💡 Tip: Set USE_REDIS=false in .env to disable Redis checks, or start Redis server")
            storage = MemoryStorage()
            logger.info("✓ Using Memory FSM storage (state will be lost on restart)")
        except Exception as e:
            logger.warning(f"⚠ Failed to initialize Redis storage ({e}), falling back to Memory storage")
            logger.info("💡 Tip: Set USE_REDIS=false in .env to disable Redis checks, or start Redis server")
            storage = MemoryStorage()
            logger.info("✓ Using Memory FSM storage (state will be lost on restart)")
    else:
        logger.info("ℹ Redis disabled (USE_REDIS=false), using Memory storage")
        storage = MemoryStorage()
        logger.info("✓ Using Memory FSM storage (state will be lost on restart)")
    
    # Create dispatcher
    dp = Dispatcher(storage=storage)
    
    # Register middleware (order matters!)
    # 1. Logging first (to log everything)
    dp.message.middleware(LoggingMiddleware())
    dp.callback_query.middleware(LoggingMiddleware())
    
    # 2. Authentication (get/create user)
    dp.message.middleware(AuthMiddleware())
    dp.callback_query.middleware(AuthMiddleware())
    
    # 3. RBAC (optional, can be per-handler)
    # Global RBAC can be added here if needed
    # dp.message.middleware(RBACMiddleware(required_permission="user.read"))
    
    logger.info("Middleware registered: Logging -> Auth")
    
    # Register routers
    dp.include_router(start_router)
    logger.info("Routers registered: start")
    
    # Register error handlers
    register_error_handlers(dp)
    
    logger.info("Dispatcher created successfully")
    return dp


def create_bot() -> Bot:
    """
    Create aiogram bot instance.
    
    Returns:
        Configured Bot instance
    """
    config = get_config()
    
    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML,
        ),
    )
    
    logger.info(f"Bot created: @{config.bot_username}")
    return bot

