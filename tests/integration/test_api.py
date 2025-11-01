"""
Integration tests for FastAPI endpoints.
"""

import pytest
from httpx import AsyncClient

from Systems.core.database import get_session_factory
from Systems.core.database.models.user import User, UserRole
from Systems.web.app import app


@pytest.fixture
async def client():
    """Create test client."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
async def test_user():
    """Create test user."""
    session_factory = get_session_factory()
    
    async with session_factory() as session:
        user = User(
            telegram_id=123456789,
            username="testuser",
            first_name="Test",
            last_name="User",
            role=UserRole.USER,
            is_active=True,
        )
        
        session.add(user)
        await session.commit()
        await session.refresh(user)
        
        yield user
        
        await session.delete(user)
        await session.commit()


@pytest.fixture
async def admin_user():
    """Create admin user."""
    session_factory = get_session_factory()
    
    async with session_factory() as session:
        user = User(
            telegram_id=987654321,
            username="admin",
            first_name="Admin",
            last_name="User",
            role=UserRole.ADMIN,
            is_active=True,
        )
        
        session.add(user)
        await session.commit()
        await session.refresh(user)
        
        yield user
        
        await session.delete(user)
        await session.commit()


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient) -> None:
    """Test health check endpoint."""
    response = await client.get("/health")
    
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_root(client: AsyncClient) -> None:
    """Test root endpoint."""
    response = await client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data


@pytest.mark.asyncio
async def test_get_current_user_unauthorized(client: AsyncClient) -> None:
    """Test getting current user without authentication."""
    response = await client.get("/api/users/me")
    
    # 401 or 403 are both valid for unauthorized requests
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_list_users_unauthorized(client: AsyncClient) -> None:
    """Test listing users without authentication."""
    response = await client.get("/api/users/")
    
    # 401 or 403 are both valid for unauthorized requests
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_list_modules_unauthorized(client: AsyncClient) -> None:
    """Test listing modules without authentication."""
    response = await client.get("/api/modules/")
    
    # 401 or 403 are both valid for unauthorized requests
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_get_stats_unauthorized(client: AsyncClient) -> None:
    """Test getting stats without authentication."""
    response = await client.get("/api/admin/stats")
    
    # 401 or 403 are both valid for unauthorized requests
    assert response.status_code in (401, 403)

