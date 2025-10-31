"""
Integration tests for settings API.
"""

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock, patch

from Systems.web.app import app
from Systems.web.auth.dependencies import get_current_user, require_admin


@pytest.fixture
async def client():
    """Create test client."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
async def authenticated_client(client, test_user):
    """Create authenticated client using dependency override."""
    async def override_get_current_user():
        return test_user
    
    # Save original if exists
    original = app.dependency_overrides.get(get_current_user)
    app.dependency_overrides[get_current_user] = override_get_current_user
    
    try:
        yield client
    finally:
        # Restore original or remove override
        if original:
            app.dependency_overrides[get_current_user] = original
        else:
            app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_get_user_settings_unauthorized(client: AsyncClient) -> None:
    """Test getting user settings without authentication."""
    response = await client.get("/api/settings/test_module/user")
    
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_update_user_setting_unauthorized(client: AsyncClient) -> None:
    """Test updating user setting without authentication."""
    response = await client.put(
        "/api/settings/test_module/user/theme",
        json={"value": "dark"},
    )
    
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_get_admin_settings_unauthorized(client: AsyncClient) -> None:
    """Test getting admin settings without authentication."""
    response = await client.get("/api/settings/test_module/admin")
    
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_update_admin_setting_unauthorized(client: AsyncClient) -> None:
    """Test updating admin setting without authentication."""
    response = await client.put(
        "/api/settings/test_module/admin/max_users",
        json={"value": 500},
    )
    
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_get_setting_schema_unauthorized(client: AsyncClient) -> None:
    """Test getting setting schema without authentication."""
    response = await client.get("/api/settings/test_module/schema")
    
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_get_user_settings_not_found(authenticated_client: AsyncClient) -> None:
    """Test getting user settings for non-existent module."""
    response = await authenticated_client.get("/api/settings/nonexistent_module/user")
    
    # API may return 200 with empty dict for non-existent module
    assert response.status_code in (200, 404)
    if response.status_code == 200:
        data = response.json()
        assert isinstance(data, dict)


@pytest.mark.asyncio
async def test_update_user_setting_not_found(authenticated_client: AsyncClient) -> None:
    """Test updating user setting for non-existent module."""
    response = await authenticated_client.put(
        "/api/settings/nonexistent_module/user/theme",
        json={"value": "dark"},
    )
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_admin_settings_not_admin(authenticated_client: AsyncClient, test_user) -> None:
    """Test getting admin settings as non-admin user."""
    # test_user is regular user, not admin
    response = await authenticated_client.get("/api/settings/test_module/admin")
    
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_update_admin_setting_not_admin(authenticated_client: AsyncClient, test_user) -> None:
    """Test updating admin setting as non-admin user."""
    # test_user is regular user, not admin
    response = await authenticated_client.put(
        "/api/settings/test_module/admin/max_users",
        json={"value": 500},
    )
    
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_get_setting_schema_not_found(authenticated_client: AsyncClient) -> None:
    """Test getting setting schema for non-existent module."""
    response = await authenticated_client.get("/api/settings/nonexistent_module/schema")
    
    assert response.status_code == 404

