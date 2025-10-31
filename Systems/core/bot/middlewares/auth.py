"""
Authentication middleware for bot handlers.
"""

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from aiogram.types.user import User as TelegramUser

from Systems.core.database.models.user import User
from Systems.core.database.repositories.user_repository import UserRepository
from Systems.core.logger import get_logger
from Systems.core.user.user_service import UserService
from Systems.core.utils.config import get_config

logger = get_logger(__name__)


class AuthMiddleware(BaseMiddleware):
    """
    Authentication middleware for aiogram handlers.
    
    Retrieves user from database and attaches to handler data.
    Creates new users on first interaction.
    
    Example:
        ```python
        dp.message.middleware(AuthMiddleware())
        ```
    """
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        """
        Process event and attach user to data.
        
        Args:
            handler: Handler function
            event: Telegram event
            data: Handler data
            
        Returns:
            Handler result
        """
        # Get Telegram user from event
        telegram_user: TelegramUser | None = None
        
        if hasattr(event, "from_user"):
            telegram_user = event.from_user
        
        if not telegram_user:
            logger.warning("AuthMiddleware: No user found in event")
            return await handler(event, data)
        
        # Get database session
        from Systems.core.database import get_session_factory
        
        session_factory = get_session_factory()
        async with session_factory() as session:
            try:
                user_service = UserService(session)
                
                # Try to get existing user
                user = await user_service.get_user(telegram_user.id)
                
                if not user:
                    # Create new user
                    logger.info(f"Creating new user: {telegram_user.id} (@{telegram_user.username})")
                    
                    config = get_config()
                    defaults = {
                        "username": telegram_user.username,
                        "first_name": telegram_user.first_name or "",
                        "last_name": telegram_user.last_name,
                        "photo_url": (
                            f"https://api.telegram.org/file/bot{config.bot_token}/"
                            f"photos/{telegram_user.id}.jpg"
                            if hasattr(telegram_user, "photo") and telegram_user.photo
                            else None
                        ),
                        "role": (
                            "super_admin"
                            if telegram_user.id == config.super_admin_id
                            else "user"
                        ),
                    }
                    
                    user, created = await user_service.get_or_create(
                        telegram_user.id,
                        defaults,
                    )
                    
                    if created:
                        logger.info(f"New user created: {telegram_user.id}")
                    
                    await session.commit()
                else:
                    # Update user info if changed
                    update_data = {}
                    
                    if user.username != telegram_user.username:
                        update_data["username"] = telegram_user.username
                    if user.first_name != (telegram_user.first_name or ""):
                        update_data["first_name"] = telegram_user.first_name or ""
                    if user.last_name != telegram_user.last_name:
                        update_data["last_name"] = telegram_user.last_name
                    
                    if update_data:
                        await user_service.update_user(telegram_user.id, update_data)
                        await session.commit()
                        logger.debug(f"User info updated: {telegram_user.id}")
                
                # Attach user to data
                data["user"] = user
                data["session"] = session
                
                logger.debug(f"User authenticated: {user.telegram_id} ({user.role.value})")
                
                result = await handler(event, data)
                await session.commit()
                return result
                
            except Exception as e:
                logger.error(f"AuthMiddleware error: {e}", exc_info=True)
                await session.rollback()
                # Continue without user if error occurs
                return await handler(event, data)

