"""
Logging middleware for bot handlers.
"""

import logging
from datetime import datetime
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from Systems.core.logger import get_logger

logger = get_logger(__name__)


class LoggingMiddleware(BaseMiddleware):
    """
    Logging middleware for aiogram handlers.
    
    Logs all messages, callbacks, and commands with user information.
    
    Example:
        ```python
        dp.message.middleware(LoggingMiddleware())
        dp.callback_query.middleware(LoggingMiddleware())
        ```
    """
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        """
        Log event and execute handler.
        
        Args:
            handler: Handler function
            event: Telegram event
            data: Handler data
            
        Returns:
            Handler result
        """
        # Get user info
        user_id = None
        username = None
        
        if isinstance(event, (Message, CallbackQuery)):
            if isinstance(event, CallbackQuery):
                user = event.from_user
            else:
                user = event.from_user
            
            user_id = user.id if user else None
            username = user.username if user else None
        
        # Get command/text
        command = None
        text = None
        
        if isinstance(event, Message):
            if event.text:
                text = event.text
                # Extract command
                if text.startswith("/"):
                    parts = text.split()
                    command = parts[0] if parts else None
        elif isinstance(event, CallbackQuery):
            command = event.data
        
        # Log event
        event_type = type(event).__name__
        log_data = {
            "event_type": event_type,
            "user_id": user_id,
            "username": username,
            "command": command,
            "text": text[:100] if text and len(text) > 100 else text,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        # Compact event logging (only for messages/callbacks, not all events)
        if isinstance(event, (Message, CallbackQuery)):
            event_info = event_type
            if user_id:
                event_info += f" | User: {user_id}"
                if username:
                    event_info += f" (@{username})"
            if command:
                event_info += f" | {command}"
            logger.debug(event_info)
        
        try:
            return await handler(event, data)
        except Exception as e:
            logger.error(f"Handler error | {event_type} | {e}", exc_info=True)
            raise

