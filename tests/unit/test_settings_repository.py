"""
Unit tests for SettingsRepository.
"""

import pytest

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from Systems.core.database import Base
from Systems.core.database.models.module_settings import SettingLevel
from Systems.core.database.repositories.settings_repository import SettingsRepository
from Systems.core.database.repositories.user_repository import UserRepository


@pytest.fixture
async def db_session():
    """Create a test database session."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session_maker = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session_maker() as session:
        yield session
    
    await engine.dispose()


@pytest.fixture
def settings_repo(db_session: AsyncSession) -> SettingsRepository:
    """Create a SettingsRepository instance."""
    return SettingsRepository(db_session)


@pytest.mark.asyncio
async def test_set_and_get_user_setting(settings_repo: SettingsRepository) -> None:
    """Test setting and getting a user setting."""
    await settings_repo.set_user_setting("test_module", 123456789, "key1", "value1")
    await settings_repo.session.commit()
    
    setting = await settings_repo.get_user_setting("test_module", 123456789, "key1")
    
    assert setting is not None
    assert setting.module_name == "test_module"
    assert setting.level == SettingLevel.USER_SETTING
    assert setting.user_id == 123456789
    assert setting.setting_key == "key1"
    assert setting.setting_value == "value1"


@pytest.mark.asyncio
async def test_update_user_setting(settings_repo: SettingsRepository) -> None:
    """Test updating an existing user setting."""
    await settings_repo.set_user_setting("test_module", 123456789, "key1", "value1")
    await settings_repo.session.commit()
    
    await settings_repo.set_user_setting("test_module", 123456789, "key1", "value2")
    await settings_repo.session.commit()
    
    setting = await settings_repo.get_user_setting("test_module", 123456789, "key1")
    
    assert setting is not None
    assert setting.setting_value == "value2"


@pytest.mark.asyncio
async def test_set_and_get_admin_setting(settings_repo: SettingsRepository) -> None:
    """Test setting and getting an admin setting."""
    await settings_repo.set_admin_setting("test_module", "admin_key", "admin_value")
    await settings_repo.session.commit()
    
    setting = await settings_repo.get_admin_setting("test_module", "admin_key")
    
    assert setting is not None
    assert setting.module_name == "test_module"
    assert setting.level == SettingLevel.ADMIN_SETTING
    assert setting.user_id is None
    assert setting.setting_key == "admin_key"
    assert setting.setting_value == "admin_value"


@pytest.mark.asyncio
async def test_update_admin_setting(settings_repo: SettingsRepository) -> None:
    """Test updating an existing admin setting."""
    await settings_repo.set_admin_setting("test_module", "admin_key", "value1")
    await settings_repo.session.commit()
    
    await settings_repo.set_admin_setting("test_module", "admin_key", "value2")
    await settings_repo.session.commit()
    
    setting = await settings_repo.get_admin_setting("test_module", "admin_key")
    
    assert setting is not None
    assert setting.setting_value == "value2"


@pytest.mark.asyncio
async def test_get_all_user_settings(settings_repo: SettingsRepository) -> None:
    """Test getting all user settings for a module."""
    # Create multiple settings
    await settings_repo.set_user_setting("test_module", 123456789, "key1", "value1")
    await settings_repo.set_user_setting("test_module", 123456789, "key2", "value2")
    await settings_repo.set_user_setting("test_module", 123456789, "key3", "value3")
    await settings_repo.session.commit()
    
    settings = await settings_repo.get_all_user_settings("test_module", 123456789)
    
    assert len(settings) == 3
    assert all(s.user_id == 123456789 for s in settings)
    assert all(s.module_name == "test_module" for s in settings)


@pytest.mark.asyncio
async def test_get_nonexistent_setting(settings_repo: SettingsRepository) -> None:
    """Test getting a non-existent setting returns None."""
    setting = await settings_repo.get_user_setting("test_module", 123456789, "nonexistent")
    
    assert setting is None


@pytest.mark.asyncio
async def test_delete_user_setting(settings_repo: SettingsRepository) -> None:
    """Test deleting a user setting."""
    await settings_repo.set_user_setting("test_module", 123456789, "key1", "value1")
    await settings_repo.session.commit()
    
    deleted = await settings_repo.delete_setting("test_module", "key1", user_id=123456789)
    await settings_repo.session.commit()
    
    assert deleted is True
    
    setting = await settings_repo.get_user_setting("test_module", 123456789, "key1")
    assert setting is None


@pytest.mark.asyncio
async def test_delete_admin_setting(settings_repo: SettingsRepository) -> None:
    """Test deleting an admin setting."""
    await settings_repo.set_admin_setting("test_module", "admin_key", "value1")
    await settings_repo.session.commit()
    
    deleted = await settings_repo.delete_setting("test_module", "admin_key", user_id=None)
    await settings_repo.session.commit()
    
    assert deleted is True
    
    setting = await settings_repo.get_admin_setting("test_module", "admin_key")
    assert setting is None


@pytest.mark.asyncio
async def test_delete_nonexistent_setting(settings_repo: SettingsRepository) -> None:
    """Test deleting a non-existent setting returns False."""
    deleted = await settings_repo.delete_setting("test_module", "nonexistent", user_id=123456789)
    
    assert deleted is False


@pytest.mark.asyncio
async def test_settings_isolation(settings_repo: SettingsRepository) -> None:
    """Test that settings are isolated by user and module."""
    # Create settings for different users
    await settings_repo.set_user_setting("module1", 111, "key1", "value1")
    await settings_repo.set_user_setting("module1", 222, "key1", "value2")
    await settings_repo.set_user_setting("module2", 111, "key1", "value3")
    await settings_repo.session.commit()
    
    setting1 = await settings_repo.get_user_setting("module1", 111, "key1")
    setting2 = await settings_repo.get_user_setting("module1", 222, "key1")
    setting3 = await settings_repo.get_user_setting("module2", 111, "key1")
    
    assert setting1 is not None
    assert setting1.setting_value == "value1"
    assert setting2 is not None
    assert setting2.setting_value == "value2"
    assert setting3 is not None
    assert setting3.setting_value == "value3"

