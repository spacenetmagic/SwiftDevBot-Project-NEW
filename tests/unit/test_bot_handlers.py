"""
Unit tests for bot handlers.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from aiogram.types import Message, User as TelegramUser
from aiogram.types.message import ContentType

from Systems.core.database.models.user import User, UserRole

# Import handlers directly to avoid importing dispatcher/main which require Redis
# These imports are safe as they don't cause circular dependencies
try:
    from Systems.core.bot.handlers.start import cmd_start, show_profile
    from Systems.core.bot.keyboards.persistent_menu import get_persistent_menu
except ImportError as e:
    # If Redis is not installed, skip these tests
    import pytest
    pytest.skip(f"Skipping bot handler tests: {e}", allow_module_level=True)


@pytest.fixture
def telegram_user():
    """Create mock Telegram user."""
    user = MagicMock(spec=TelegramUser)
    user.id = 123456789
    user.username = "testuser"
    user.first_name = "Test"
    user.last_name = "User"
    return user


@pytest.fixture
def db_user():
    """Create mock database user."""
    user = User(
        telegram_id=123456789,
        username="testuser",
        first_name="Test",
        last_name="User",
        role=UserRole.USER,
        is_active=True,
    )
    return user


@pytest.fixture
def message(telegram_user):
    """Create mock message."""
    msg = MagicMock(spec=Message)
    msg.from_user = telegram_user
    msg.answer = AsyncMock()
    msg.text = "/start"
    return msg


@pytest.mark.asyncio
async def test_cmd_start_user(message, db_user) -> None:
    """Test /start command for regular user."""
    await cmd_start(message, db_user)
    
    message.answer.assert_called_once()
    call_args = message.answer.call_args
    assert "Добро пожаловать" in call_args[0][0]
    assert call_args[1]["reply_markup"] is not None


@pytest.mark.asyncio
async def test_cmd_start_admin(message, db_user) -> None:
    """Test /start command for admin."""
    db_user.role = UserRole.ADMIN
    await cmd_start(message, db_user)
    
    message.answer.assert_called_once()
    call_args = message.answer.call_args
    assert "Администратор" in call_args[0][0]


@pytest.mark.asyncio
async def test_cmd_start_super_admin(message, db_user) -> None:
    """Test /start command for super admin."""
    db_user.role = UserRole.SUPER_ADMIN
    await cmd_start(message, db_user)
    
    message.answer.assert_called_once()
    call_args = message.answer.call_args
    assert "Супер-администратор" in call_args[0][0]


@pytest.mark.asyncio
async def test_show_profile(message, db_user) -> None:
    """Test profile handler."""
    await show_profile(message, db_user)
    
    message.answer.assert_called_once()
    call_args = message.answer.call_args
    assert "Профиль" in call_args[0][0]
    assert str(db_user.telegram_id) in call_args[0][0]


@pytest.mark.asyncio
async def test_get_persistent_menu_user() -> None:
    """Test persistent menu for user role."""
    keyboard = get_persistent_menu(UserRole.USER)
    
    assert keyboard is not None
    assert keyboard.keyboard is not None
    # Check buttons
    buttons_text = [btn[0].text for row in keyboard.keyboard for btn in [row]]
    assert "📋 Профиль" in buttons_text
    assert "🧩 Модули" in buttons_text
    assert "💬 Обратная связь" in buttons_text


@pytest.mark.asyncio
async def test_get_persistent_menu_moderator() -> None:
    """Test persistent menu for moderator role."""
    keyboard = get_persistent_menu(UserRole.MODERATOR)
    
    buttons_text = [btn[0].text for row in keyboard.keyboard for btn in [row]]
    assert "🛡️ Модерация" in buttons_text


@pytest.mark.asyncio
async def test_get_persistent_menu_admin() -> None:
    """Test persistent menu for admin role."""
    keyboard = get_persistent_menu(UserRole.ADMIN)
    
    buttons_text = [btn[0].text for row in keyboard.keyboard for btn in [row]]
    assert "⚙️ Админка" in buttons_text


@pytest.mark.asyncio
async def test_get_persistent_menu_super_admin() -> None:
    """Test persistent menu for super admin role."""
    keyboard = get_persistent_menu(UserRole.SUPER_ADMIN)
    
    buttons_text = [btn[0].text for row in keyboard.keyboard for btn in [row]]
    assert "⚙️ Админка" in buttons_text

