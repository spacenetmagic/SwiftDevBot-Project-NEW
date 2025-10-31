"""
Unit tests for UserService.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from Systems.core.database import Base
from Systems.core.database.models.user import User, UserRole
from Systems.core.user.user_service import UserService


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
def user_service(db_session: AsyncSession) -> UserService:
    """Create UserService instance."""
    return UserService(db_session)


@pytest.mark.asyncio
async def test_get_user_existing(user_service: UserService) -> None:
    """Test getting an existing user."""
    user_data = {
        "telegram_id": 123456789,
        "username": "testuser",
        "first_name": "Test",
        "role": UserRole.USER,
    }
    
    await user_service.create_user(123456789, user_data)
    
    user = await user_service.get_user(123456789)
    
    assert user is not None
    assert user.telegram_id == 123456789
    assert user.username == "testuser"


@pytest.mark.asyncio
async def test_get_user_nonexistent(user_service: UserService) -> None:
    """Test getting a non-existent user."""
    user = await user_service.get_user(999999999)
    
    assert user is None


@pytest.mark.asyncio
async def test_create_user(user_service: UserService) -> None:
    """Test creating a new user."""
    user_data = {
        "username": "newuser",
        "first_name": "New",
        "role": UserRole.USER,
    }
    
    user = await user_service.create_user(123456789, user_data, created_by=999999999)
    
    assert user.telegram_id == 123456789
    assert user.username == "newuser"
    
    # Check audit log
    audit_repo = user_service.audit_repo
    logs = await audit_repo.get_logs(999999999, limit=10)
    assert len(logs) > 0
    assert logs[0].action == "user.create"


@pytest.mark.asyncio
async def test_create_duplicate_user(user_service: UserService) -> None:
    """Test creating duplicate user raises ValueError."""
    user_data = {
        "username": "testuser",
        "first_name": "Test",
        "role": UserRole.USER,
    }
    
    await user_service.create_user(123456789, user_data)
    
    with pytest.raises(ValueError, match="already exists"):
        await user_service.create_user(123456789, user_data)


@pytest.mark.asyncio
async def test_update_user(user_service: UserService) -> None:
    """Test updating user."""
    user_data = {
        "username": "testuser",
        "first_name": "Test",
        "role": UserRole.USER,
    }
    
    await user_service.create_user(123456789, user_data)
    
    updated = await user_service.update_user(
        123456789,
        {"username": "updateduser", "first_name": "Updated"},
        updated_by=999999999,
    )
    
    assert updated is not None
    assert updated.username == "updateduser"
    assert updated.first_name == "Updated"
    
    # Check audit log
    logs = await user_service.audit_repo.get_logs(999999999, limit=10)
    assert any(log.action == "user.update" for log in logs)


@pytest.mark.asyncio
async def test_get_or_create_existing(user_service: UserService) -> None:
    """Test get_or_create with existing user."""
    user_data = {
        "username": "testuser",
        "first_name": "Test",
        "role": UserRole.USER,
    }
    
    await user_service.create_user(123456789, user_data)
    
    user, created = await user_service.get_or_create(123456789)
    
    assert user is not None
    assert created is False


@pytest.mark.asyncio
async def test_get_or_create_new(user_service: UserService) -> None:
    """Test get_or_create with new user."""
    defaults = {
        "username": "newuser",
        "first_name": "New",
    }
    
    user, created = await user_service.get_or_create(123456789, defaults)
    
    assert user is not None
    assert created is True
    assert user.username == "newuser"


@pytest.mark.asyncio
async def test_change_user_role(user_service: UserService) -> None:
    """Test changing user role."""
    user_data = {
        "username": "testuser",
        "first_name": "Test",
        "role": UserRole.USER,
    }
    
    await user_service.create_user(123456789, user_data)
    
    updated = await user_service.change_user_role(
        123456789,
        UserRole.ADMIN,
        changed_by=999999999,
    )
    
    assert updated is not None
    assert updated.role == UserRole.ADMIN
    
    # Check audit log
    logs = await user_service.audit_repo.get_logs(999999999, limit=10)
    assert any(log.action == "user.role_change" for log in logs)


@pytest.mark.asyncio
async def test_change_super_admin_role(user_service: UserService) -> None:
    """Test that changing super_admin role raises ValueError."""
    user_data = {
        "username": "admin",
        "first_name": "Admin",
        "role": UserRole.SUPER_ADMIN,
    }
    
    await user_service.create_user(123456789, user_data)
    
    with pytest.raises(ValueError, match="Cannot change super_admin"):
        await user_service.change_user_role(123456789, UserRole.USER)


@pytest.mark.asyncio
async def test_grant_permission(user_service: UserService) -> None:
    """Test granting permission."""
    user_data = {
        "username": "testuser",
        "first_name": "Test",
        "role": UserRole.USER,
    }
    
    await user_service.create_user(123456789, user_data)
    
    updated = await user_service.grant_permission(
        123456789,
        "special.permission",
        granted_by=999999999,
    )
    
    assert updated is not None
    assert "special.permission" in updated.custom_permissions
    
    # Check audit log
    logs = await user_service.audit_repo.get_logs(999999999, limit=10)
    assert any(log.action == "user.permission.grant" for log in logs)


@pytest.mark.asyncio
async def test_revoke_permission(user_service: UserService) -> None:
    """Test revoking permission."""
    user_data = {
        "username": "testuser",
        "first_name": "Test",
        "role": UserRole.USER,
        "custom_permissions": ["special.permission"],
    }
    
    await user_service.create_user(123456789, user_data)
    
    updated = await user_service.revoke_permission(
        123456789,
        "special.permission",
        revoked_by=999999999,
    )
    
    assert updated is not None
    assert "special.permission" not in updated.custom_permissions
    
    # Check audit log
    logs = await user_service.audit_repo.get_logs(999999999, limit=10)
    assert any(log.action == "user.permission.revoke" for log in logs)


@pytest.mark.asyncio
async def test_get_user_permissions(user_service: UserService) -> None:
    """Test getting user permissions."""
    user_data = {
        "username": "admin",
        "first_name": "Admin",
        "role": UserRole.ADMIN,
        "custom_permissions": ["custom.permission"],
    }
    
    await user_service.create_user(123456789, user_data)
    user = await user_service.get_user(123456789)
    
    permissions = await user_service.get_user_permissions(user)
    
    # Should have role permissions + custom permissions
    assert "user.write" in permissions  # Admin role permission
    assert "custom.permission" in permissions  # Custom permission


@pytest.mark.asyncio
async def test_list_users(user_service: UserService) -> None:
    """Test listing users."""
    # Create multiple users
    for i in range(5):
        user_data = {
            "username": f"user{i}",
            "first_name": f"User{i}",
            "role": UserRole.USER,
        }
        await user_service.create_user(100000000 + i, user_data)
    
    users = await user_service.list_users(skip=0, limit=10)
    
    assert len(users) == 5


@pytest.mark.asyncio
async def test_list_users_by_role(user_service: UserService) -> None:
    """Test listing users filtered by role."""
    # Create users with different roles
    await user_service.create_user(1001, {
        "username": "admin1",
        "first_name": "Admin1",
        "role": UserRole.ADMIN,
    })
    await user_service.create_user(1002, {
        "username": "admin2",
        "first_name": "Admin2",
        "role": UserRole.ADMIN,
    })
    await user_service.create_user(2001, {
        "username": "user1",
        "first_name": "User1",
        "role": UserRole.USER,
    })
    
    admins = await user_service.list_users(role=UserRole.ADMIN)
    
    assert len(admins) == 2
    assert all(user.role == UserRole.ADMIN for user in admins)

