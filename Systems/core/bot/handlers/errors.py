"""
Error handlers for bot.
"""

from typing import Any

from aiogram import Dispatcher, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.types import ErrorEvent, Message, Update

from Systems.core.logger import get_logger

logger = get_logger(__name__)

router = Router(name="errors")


async def handle_telegram_api_error(event: ErrorEvent, exception: TelegramAPIError) -> bool:
    """
    Handle Telegram API errors.
    
    Args:
        event: Error event
        exception: Telegram API exception
        
    Returns:
        True if handled, False otherwise
    """
    logger.error(f"Telegram API error: {exception}")
    
    # Try to send error message to user if possible
    if isinstance(event.update, Update):
        if event.update.message:
            try:
                await event.update.message.answer(
                    "❌ Произошла ошибка при обработке запроса. Попробуйте позже."
                )
            except Exception as e:
                logger.error(f"Failed to send error message: {e}")
    
    return True


async def handle_unknown_command(message: Message) -> None:
    """
    Handle unknown commands.
    
    Args:
        message: Telegram message
    """
    logger.warning(f"Unknown command from user {message.from_user.id}: {message.text}")
    
    await message.answer(
        "❓ Неизвестная команда.\n\n"
        "Используйте /start для начала работы или выберите действие из меню."
    )


async def handle_unhandled_error(event: ErrorEvent, exception: Exception) -> bool:
    """
    Handle unhandled exceptions.
    
    Args:
        event: Error event
        exception: Exception
        
    Returns:
        True if handled, False otherwise
    """
    logger.error(
        f"Unhandled error: {exception}",
        exc_info=True,
    )
    
    # Try to send error message to user
    if isinstance(event.update, Update):
        if event.update.message:
            try:
                await event.update.message.answer(
                    "❌ Произошла внутренняя ошибка. "
                    "Мы уже работаем над её устранением."
                )
            except Exception:
                pass
    
    return True


def register_error_handlers(dp: Dispatcher) -> None:
    """
    Register error handlers with dispatcher.
    
    Args:
        dp: Aiogram dispatcher
    """
    # Register handlers
    dp.errors.register(handle_telegram_api_error)
    dp.errors.register(handle_unhandled_error)
    
    # Register unknown command handler
    router.message.register(handle_unknown_command)
    dp.include_router(router)
    
    logger.info("Error handlers registered")

