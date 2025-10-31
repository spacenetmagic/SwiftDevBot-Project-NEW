"""
Start command handler.
"""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from Systems.core.bot.keyboards.persistent_menu import get_persistent_menu
from Systems.core.database.models.user import User
from Systems.core.logger import get_logger

logger = get_logger(__name__)

router = Router(name="start")


@router.message(Command("start"))
async def cmd_start(message: Message, user: User) -> None:
    """
    Handle /start command.
    
    Shows welcome message and persistent menu based on user role.
    
    Args:
        message: Telegram message
        user: User object from AuthMiddleware
    """
    logger.info(f"Start command from user: {user.telegram_id}")
    
    # Get role-based menu
    keyboard = get_persistent_menu(user.role)
    
    # Welcome message based on role
    role_messages = {
        "super_admin": (
            "👋 Добро пожаловать, Супер-администратор!\n\n"
            "У вас есть полный доступ ко всем функциям бота.\n"
            "Выберите действие из меню:"
        ),
        "admin": (
            "👋 Добро пожаловать, Администратор!\n\n"
            "У вас есть доступ к административным функциям.\n"
            "Выберите действие из меню:"
        ),
        "moderator": (
            "👋 Добро пожаловать, Модератор!\n\n"
            "У вас есть доступ к функциям модерации.\n"
            "Выберите действие из меню:"
        ),
        "user": (
            "👋 Добро пожаловать!\n\n"
            "Я SwiftDevBot - модульный Telegram бот.\n"
            "Выберите действие из меню:"
        ),
    }
    
    role_value = user.role.value if hasattr(user.role, "value") else str(user.role)
    welcome_text = role_messages.get(role_value, role_messages["user"])
    
    await message.answer(
        welcome_text,
        reply_markup=keyboard,
    )
    
    logger.debug(f"Start command handled for user: {user.telegram_id}")


@router.message(lambda msg: msg.text == "📋 Профиль")
async def show_profile(message: Message, user: User) -> None:
    """
    Show user profile.
    
    Args:
        message: Telegram message
        user: User object
    """
    logger.info(f"Profile request from user: {user.telegram_id}")
    
    profile_text = (
        f"👤 **Профиль**\n\n"
        f"🆔 ID: `{user.telegram_id}`\n"
        f"👤 Имя: {user.first_name}"
    )
    
    if user.last_name:
        profile_text += f" {user.last_name}"
    
    if user.username:
        profile_text += f"\n📝 Username: @{user.username}"
    
    profile_text += (
        f"\n🎭 Роль: {user.role.value}\n"
        f"✅ Статус: {'Активен' if user.is_active else 'Неактивен'}\n"
        f"📅 Создан: {user.created_at.strftime('%Y-%m-%d %H:%M') if user.created_at else 'N/A'}"
    )
    
    await message.answer(profile_text, parse_mode="Markdown")
    logger.debug(f"Profile sent for user: {user.telegram_id}")

