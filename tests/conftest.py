"""
Pytest configuration and fixtures.
"""

import asyncio
from typing import AsyncGenerator, Generator

import pytest
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from Systems.core.database import get_session_factory, init_db
from Systems.core.database.models.user import User, UserRole
from Systems.core.utils.config import Config
from Systems.core.modules.base_module import BaseModule
from Systems.core.modules.manifest import ModuleManifest


# Pytest fixtures


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator:
    """
    Create in-memory SQLite database session for tests.
    
    Returns:
        Async database session
    """
    # Create in-memory SQLite database
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True,
    )
    
    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    # Create tables
    async with engine.begin() as conn:
        # Import Base from database package
        from Systems.core.database import Base
        # Import all models to register them with Base
        from Systems.core.database.models.user import User
        from Systems.core.database.models.module_settings import ModuleSetting
        from Systems.core.database.models.audit_log import AuditLog
        
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async with async_session() as session:
        yield session
        await session.rollback()
    
    # Cleanup
    await engine.dispose()


@pytest.fixture
async def test_user(db_session) -> User:
    """
    Create a test user.
    
    Returns:
        Test user instance
    """
    user = User(
        telegram_id=123456789,
        username="testuser",
        first_name="Test",
        last_name="User",
        role=UserRole.USER,
        is_active=True,
    )
    
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    return user


@pytest.fixture
async def test_admin(db_session) -> User:
    """
    Create a test admin user.
    
    Returns:
        Test admin user instance
    """
    user = User(
        telegram_id=987654321,
        username="admin",
        first_name="Admin",
        last_name="User",
        role=UserRole.ADMIN,
        is_active=True,
    )
    
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    return user


@pytest.fixture
async def test_super_admin(db_session) -> User:
    """
    Create a test super admin user.
    
    Returns:
        Test super admin user instance
    """
    user = User(
        telegram_id=111111111,
        username="superadmin",
        first_name="Super",
        last_name="Admin",
        role=UserRole.SUPER_ADMIN,
        is_active=True,
    )
    
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    return user


@pytest.fixture
def mock_redis():
    """
    Create mock Redis client.
    
    Returns:
        Mock Redis client
    """
    redis_mock = MagicMock()
    redis_mock.get = AsyncMock(return_value=None)
    redis_mock.set = AsyncMock(return_value=True)
    redis_mock.delete = AsyncMock(return_value=1)
    redis_mock.exists = AsyncMock(return_value=False)
    redis_mock.zadd = AsyncMock(return_value=1)
    redis_mock.zrange = AsyncMock(return_value=[])
    redis_mock.zcard = AsyncMock(return_value=0)
    redis_mock.lpush = AsyncMock(return_value=1)
    redis_mock.lrange = AsyncMock(return_value=[])
    redis_mock.close = AsyncMock()
    
    return redis_mock


@pytest.fixture
def mock_bot():
    """
    Create mock Telegram bot.
    
    Returns:
        Mock bot instance
    """
    bot = MagicMock()
    bot.token = "test_token"
    bot.username = "test_bot"
    bot.get_me = AsyncMock(return_value=MagicMock(username="test_bot"))
    
    return bot


@pytest.fixture
def mock_dispatcher():
    """
    Create mock dispatcher.
    
    Returns:
        Mock dispatcher instance
    """
    dispatcher = MagicMock()
    dispatcher.include_router = MagicMock()
    dispatcher.middleware.setup = MagicMock()
    
    return dispatcher


@pytest.fixture
def sample_module_manifest() -> ModuleManifest:
    """
    Create sample module manifest.
    
    Returns:
        ModuleManifest instance
    """
    return ModuleManifest(
        name="test_module",
        display_name="Test Module",
        version="1.0.0",
        description="Test module for testing",
        author="Test Author",
        dependencies=[],
        commands=[
            {"name": "test", "description": "Test command", "admin": False},
        ],
        settings={
            "theme": {
                "type": "string",
                "default": "light",
                "description": "Theme setting",
            },
        },
        languages=["en"],
        background_tasks=["cleanup_task"],
        enabled_by_default=False,
    )


@pytest.fixture
def sample_module(sample_module_manifest, db_session) -> BaseModule:
    """
    Create sample module instance.
    
    Returns:
        BaseModule instance
    """
    from Systems.core.database.repositories.settings_repository import SettingsRepository
    
    settings_repo = SettingsRepository(db_session)
    
    class TestModule(BaseModule):
        async def on_load(self) -> None:
            pass
        
        async def on_unload(self) -> None:
            pass
    
    return TestModule(sample_module_manifest, settings_repo)


@pytest.fixture
def mock_config():
    """
    Create mock configuration.
    
    Returns:
        Mock Config instance
    """
    config = MagicMock(spec=Config)
    config.bot_token = "test_token"
    config.bot_username = "test_bot"
    config.super_admin_id = 111111111
    config.db_type = "memory"
    config.db_host = "localhost"
    config.db_port = 5432
    config.db_name = "test_db"
    config.db_user = "test_user"
    config.db_password = "test_pass"
    config.redis_host = "localhost"
    config.redis_port = 6379
    config.web_panel_url = "http://localhost:8000"
    config.jwt_secret = "test_secret_key_minimum_32_characters_long"
    config.log_level = "INFO"
    
    return config


@pytest.fixture
def mock_event_bus():
    """
    Create mock event bus.
    
    Returns:
        Mock event bus instance
    """
    event_bus = MagicMock()
    event_bus.emit = AsyncMock()
    event_bus.subscribe = AsyncMock()
    event_bus.unsubscribe = AsyncMock()
    event_bus.get_handlers = MagicMock(return_value=[])
    
    return event_bus


@pytest.fixture
def mock_telegram_message():
    """
    Create mock Telegram message.
    
    Returns:
        Mock message instance
    """
    message = MagicMock()
    message.from_user = MagicMock()
    message.from_user.id = 123456789
    message.from_user.username = "testuser"
    message.from_user.first_name = "Test"
    message.from_user.last_name = "User"
    message.text = "/start"
    message.answer = AsyncMock()
    message.reply = AsyncMock()
    
    return message


@pytest.fixture
def mock_telegram_callback():
    """
    Create mock Telegram callback query.
    
    Returns:
        Mock callback query instance
    """
    callback = MagicMock()
    callback.from_user = MagicMock()
    callback.from_user.id = 123456789
    callback.data = "test_callback"
    callback.message = MagicMock()
    callback.message.answer = AsyncMock()
    callback.answer = AsyncMock()
    
    return callback


# Mock patching fixtures


@pytest.fixture
def mock_load_config(mock_config):
    """
    Mock load_config function.
    
    Returns:
        Mock config
    """
    with patch("Systems.core.utils.config.Config", return_value=mock_config):
        yield mock_config


@pytest.fixture
def mock_get_session_factory(db_session):
    """
    Mock get_session_factory function.
    
    Returns:
        Session factory mock
    """
    def session_factory():
        return MagicMock(
            __aenter__=AsyncMock(return_value=db_session),
            __aexit__=AsyncMock(return_value=None),
        )
    
    with patch("Systems.core.database.get_session_factory", return_value=session_factory):
        yield session_factory

