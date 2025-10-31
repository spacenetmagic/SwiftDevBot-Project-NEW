"""
Persistent menu keyboards for bot.
"""

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from Systems.core.database.models.user import UserRole
from Systems.core.logger import get_logger

logger = get_logger(__name__)


def get_persistent_menu(role: UserRole | str) -> ReplyKeyboardMarkup:
    """
    Get persistent menu keyboard based on user role.
    
    Args:
        role: User role (UserRole enum or string)
        
    Returns:
        ReplyKeyboardMarkup with role-appropriate buttons
        
    Example:
        ```python
        keyboard = get_persistent_menu(UserRole.ADMIN)
        await message.answer("Выберите действие:", reply_markup=keyboard)
        ```
    """
    # Convert role to string if needed
    role_value = role.value if hasattr(role, "value") else str(role)
    
    # Base buttons for all users
    buttons = [
        [KeyboardButton(text="📋 Профиль")],
        [KeyboardButton(text="🧩 Модули")],
    ]
    
    # Role-specific buttons
    if role_value in ("admin", "super_admin"):
        buttons.append([KeyboardButton(text="⚙️ Админка")])
    elif role_value == "moderator":
        buttons.append([KeyboardButton(text="🛡️ Модерация")])
    else:
        buttons.append([KeyboardButton(text="💬 Обратная связь")])
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        persistent=True,
        input_field_placeholder="Выберите действие из меню",
    )
    
    logger.debug(f"Generated persistent menu for role: {role_value}")
    return keyboard

