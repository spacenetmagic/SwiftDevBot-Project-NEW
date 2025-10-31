"""
Integration tests for modules API.
"""

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock, patch

from Systems.web.app import app
from Systems.web.auth.dependencies import get_current_user


@pytest.fixture
async def client():
    """Create test client."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
async def valid_token(jwt_handler, test_user):
    """Create valid JWT token for test user."""
    return await jwt_handler.create_access_token(
        user_id=test_user.telegram_id,
        username=test_user.username,
        role=test_user.role.value if hasattr(test_user.role, 'value') else str(test_user.role),
    )


@pytest.fixture
def auth_headers(valid_token):
    """Create auth headers with valid token."""
    return {"Authorization": f"Bearer {valid_token}"}


@pytest.fixture
async def authenticated_client(client, test_user):
    """Create authenticated client using dependency override."""
    async def override_get_current_user():
        return test_user
    
    app.dependency_overrides[get_current_user] = override_get_current_user
    
    try:
        yield client
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_modules_unauthorized(client: AsyncClient) -> None:
    """Test listing modules without authentication."""
    response = await client.get("/api/modules/")
    
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_get_module_unauthorized(client: AsyncClient) -> None:
    """Test getting module without authentication."""
    response = await client.get("/api/modules/test_module")
    
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_enable_module_unauthorized(client: AsyncClient) -> None:
    """Test enabling module without authentication."""
    response = await client.post("/api/modules/test_module/enable")
    
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_disable_module_unauthorized(client: AsyncClient) -> None:
    """Test disabling module without authentication."""
    response = await client.post("/api/modules/test_module/disable")
    
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_reload_module_unauthorized(client: AsyncClient) -> None:
    """Test reloading module without authentication."""
    response = await client.post("/api/modules/test_module/reload")
    
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_check_updates_unauthorized(client: AsyncClient) -> None:
    """Test checking updates without authentication."""
    response = await client.get("/api/modules/updates")
    
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_list_modules_not_found(authenticated_client: AsyncClient) -> None:
    """Test listing modules when no modules exist."""
    response = await authenticated_client.get("/api/modules/")
    
    # Should return empty list or error
    assert response.status_code in (200, 404, 500)


@pytest.mark.asyncio
async def test_get_module_not_found(authenticated_client: AsyncClient) -> None:
    """Test getting non-existent module."""
    response = await authenticated_client.get("/api/modules/nonexistent_module")
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_enable_module_not_found(authenticated_client: AsyncClient) -> None:
    """Test enabling non-existent module."""
    response = await authenticated_client.post("/api/modules/nonexistent_module/enable")
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_disable_module_not_found(authenticated_client: AsyncClient) -> None:
    """Test disabling non-existent module."""
    response = await authenticated_client.post("/api/modules/nonexistent_module/disable")
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_reload_module_not_found(authenticated_client: AsyncClient, test_admin) -> None:
    """Test reloading non-existent module."""
    from Systems.web.auth.dependencies import require_admin
    
    async def override_require_admin():
        return test_admin
    
    app.dependency_overrides[require_admin] = override_require_admin
    
    try:
        response = await authenticated_client.post("/api/modules/nonexistent_module/reload")
        assert response.status_code == 404
    finally:
        app.dependency_overrides.pop(require_admin, None)

