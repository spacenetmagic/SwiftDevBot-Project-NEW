"""
Command handlers for example module.

This file demonstrates how to register command handlers with aiogram.
"""

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

from Systems.core.logger import get_logger
from Systems.core.rbac.middleware import require_role
from Systems.core.database.models.user import UserRole

logger = get_logger(__name__)

# Create router for this module
router = Router(name="example_module_commands")


@router.message(Command("example"))
async def handle_example_command(message: Message) -> None:
    """
    Handle /example command.
    
    This command is available to all users.
    
    Args:
        message: Telegram message object
    """
    logger.info(f"Example command received from user: {message.from_user.id}")
    
    # Get module instance (you can access it through dependency injection or context)
    # For now, this is a simple example
    
    await message.answer(
        "👋 Example command executed!\n\n"
        "This is an example command handler demonstrating module functionality."
    )


@router.message(Command("example_admin"))
@require_role(UserRole.ADMIN)  # Only admins can use this command
async def handle_example_admin_command(message: Message) -> None:
    """
    Handle /example_admin command (admin-only).
    
    This command is only available to admins.
    
    Args:
        message: Telegram message object
    """
    logger.info(f"Example admin command received from admin: {message.from_user.id}")
    
    await message.answer(
        "🛡️ Admin command executed!\n\n"
        "This command is only available to administrators."
    )


# You can register this router in module.py's on_load() method:
# self.router.include_router(router)

