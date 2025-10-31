"""
Unit tests for SettingsManager.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from Systems.core.database.repositories.settings_repository import SettingsRepository
from Systems.core.modules.manifest import ModuleManifest
from Systems.core.modules.settings_manager import SettingsManager


@pytest.fixture
def settings_repo(db_session):
    """Create SettingsRepository instance."""
    return SettingsRepository(db_session)


@pytest.fixture
def settings_manager(settings_repo):
    """Create SettingsManager instance."""
    return SettingsManager(settings_repo)


@pytest.fixture
def sample_manifest():
    """Create sample module manifest."""
    return ModuleManifest(
        name="test_module",
        display_name="Test Module",
        version="1.0.0",
        settings={
            "theme": {
                "type": "string",
                "default": "light",
            },
            "max_users": {
                "type": "integer",
                "default": 100,
                "min": 1,
                "max": 1000,
            },
        },
    )


@pytest.mark.asyncio
async def test_get_user_setting(settings_manager, settings_repo, test_user, sample_manifest) -> None:
    """Test getting user setting."""
    # Set a setting first
    await settings_repo.set_user_setting("test_module", test_user.telegram_id, "theme", "dark")
    await settings_repo.session.commit()
    
    # Get setting
    value = await settings_manager.get_user_setting("test_module", test_user.telegram_id, "theme")
    
    assert value == "dark"


@pytest.mark.asyncio
async def test_get_user_setting_not_found(settings_manager, test_user) -> None:
    """Test getting user setting that doesn't exist."""
    value = await settings_manager.get_user_setting(
        "test_module", test_user.telegram_id, "nonexistent", default="default"
    )
    
    assert value == "default"


@pytest.mark.asyncio
async def test_set_user_setting(settings_manager, settings_repo, test_user, sample_manifest) -> None:
    """Test setting user setting."""
    await settings_manager.set_user_setting(
        "test_module", test_user.telegram_id, "theme", "dark", manifest=sample_manifest
    )
    
    # Verify setting was saved
    setting = await settings_repo.get_user_setting("test_module", test_user.telegram_id, "theme")
    assert setting is not None
    assert setting.setting_value == "dark"


@pytest.mark.asyncio
async def test_set_user_setting_validation_error(settings_manager, test_user, sample_manifest) -> None:
    """Test setting user setting with invalid type."""
    # Try to set integer field with string
    with pytest.raises(ValueError, match="expects integer"):
        await settings_manager.set_user_setting(
            "test_module", test_user.telegram_id, "max_users", "not_a_number", manifest=sample_manifest
        )


@pytest.mark.asyncio
async def test_set_user_setting_min_validation(settings_manager, test_user, sample_manifest) -> None:
    """Test setting user setting with value below minimum."""
    with pytest.raises(ValueError, match="below minimum"):
        await settings_manager.set_user_setting(
            "test_module", test_user.telegram_id, "max_users", 0, manifest=sample_manifest
        )


@pytest.mark.asyncio
async def test_set_user_setting_max_validation(settings_manager, test_user, sample_manifest) -> None:
    """Test setting user setting with value above maximum."""
    with pytest.raises(ValueError, match="above maximum"):
        await settings_manager.set_user_setting(
            "test_module", test_user.telegram_id, "max_users", 2000, manifest=sample_manifest
        )


@pytest.mark.asyncio
async def test_get_admin_setting(settings_manager, settings_repo, sample_manifest) -> None:
    """Test getting admin setting."""
    # Set admin setting first
    await settings_repo.set_admin_setting("test_module", "max_users", 200)
    await settings_repo.session.commit()
    
    # Get setting
    value = await settings_manager.get_admin_setting("test_module", "max_users")
    
    assert value == 200


@pytest.mark.asyncio
async def test_get_admin_setting_not_found(settings_manager) -> None:
    """Test getting admin setting that doesn't exist."""
    value = await settings_manager.get_admin_setting("test_module", "nonexistent", default=100)
    
    assert value == 100


@pytest.mark.asyncio
async def test_set_admin_setting(settings_manager, settings_repo, sample_manifest) -> None:
    """Test setting admin setting."""
    await settings_manager.set_admin_setting(
        "test_module", "max_users", 500, manifest=sample_manifest
    )
    
    # Verify setting was saved
    setting = await settings_repo.get_admin_setting("test_module", "max_users")
    assert setting is not None
    assert setting.setting_value == 500


@pytest.mark.asyncio
async def test_set_admin_setting_validation_error(settings_manager, sample_manifest) -> None:
    """Test setting admin setting with invalid type."""
    with pytest.raises(ValueError, match="expects integer"):
        await settings_manager.set_admin_setting(
            "test_module", "max_users", "not_a_number", manifest=sample_manifest
        )


@pytest.mark.asyncio
async def test_set_setting_without_manifest(settings_manager, settings_repo, test_user) -> None:
    """Test setting setting without manifest validation."""
    # Should work without validation
    await settings_manager.set_user_setting(
        "test_module", test_user.telegram_id, "any_key", "any_value"
    )
    
    # Verify setting was saved
    setting = await settings_repo.get_user_setting("test_module", test_user.telegram_id, "any_key")
    assert setting is not None
    assert setting.setting_value == "any_value"

