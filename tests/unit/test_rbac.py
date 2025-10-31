"""
Unit tests for RBAC system.
"""

import pytest

from Systems.core.database.models.user import User, UserRole
from Systems.core.rbac.rbac import RBAC


@pytest.fixture
def rbac() -> RBAC:
    """Create RBAC instance."""
    return RBAC()


@pytest.fixture
def super_admin_user() -> User:
    """Create super admin user."""
    user = User(
        telegram_id=123456789,
        username="superadmin",
        first_name="Super",
        role=UserRole.SUPER_ADMIN,
        is_active=True,
    )
    return user


@pytest.fixture
def admin_user() -> User:
    """Create admin user."""
    user = User(
        telegram_id=999999999,
        username="admin",
        first_name="Admin",
        role=UserRole.ADMIN,
        is_active=True,
    )
    return user


@pytest.fixture
def moderator_user() -> User:
    """Create moderator user."""
    user = User(
        telegram_id=888888888,
        username="moderator",
        first_name="Mod",
        role=UserRole.MODERATOR,
        is_active=True,
    )
    return user


@pytest.fixture
def regular_user() -> User:
    """Create regular user."""
    user = User(
        telegram_id=777777777,
        username="user",
        first_name="User",
        role=UserRole.USER,
        is_active=True,
    )
    return user


@pytest.mark.asyncio
async def test_get_role_permissions_super_admin(rbac: RBAC) -> None:
    """Test getting super admin permissions."""
    perms = rbac.get_role_permissions(UserRole.SUPER_ADMIN)
    
    assert "*" in perms


@pytest.mark.asyncio
async def test_get_role_permissions_admin(rbac: RBAC) -> None:
    """Test getting admin permissions."""
    perms = rbac.get_role_permissions(UserRole.ADMIN)
    
    assert "user.write" in perms
    assert "module.install" in perms
    assert "admin.access" in perms


@pytest.mark.asyncio
async def test_get_role_permissions_moderator(rbac: RBAC) -> None:
    """Test getting moderator permissions."""
    perms = rbac.get_role_permissions(UserRole.MODERATOR)
    
    assert "user.read" in perms
    assert "content.moderate" in perms


@pytest.mark.asyncio
async def test_get_role_permissions_user(rbac: RBAC) -> None:
    """Test getting user permissions."""
    perms = rbac.get_role_permissions(UserRole.USER)
    
    assert "user.read_own" in perms


@pytest.mark.asyncio
async def test_check_permission_super_admin_wildcard(rbac: RBAC, super_admin_user: User) -> None:
    """Test super admin has all permissions via wildcard."""
    # Super admin should have any permission
    assert await rbac.check_permission(super_admin_user, "any.permission") is True
    assert await rbac.check_permission(super_admin_user, "user.write") is True
    assert await rbac.check_permission(super_admin_user, "admin.access") is True


@pytest.mark.asyncio
async def test_check_permission_admin(rbac: RBAC, admin_user: User) -> None:
    """Test admin permissions."""
    assert await rbac.check_permission(admin_user, "user.write") is True
    assert await rbac.check_permission(admin_user, "module.install") is True
    assert await rbac.check_permission(admin_user, "admin.access") is True
    
    # Admin should not have super admin permissions
    # (but we check if they have specific permissions they shouldn't)
    # Actually, admin has access to admin.access which is their permission


@pytest.mark.asyncio
async def test_check_permission_denied(rbac: RBAC, regular_user: User) -> None:
    """Test permission denied for regular user."""
    assert await rbac.check_permission(regular_user, "user.write") is False
    assert await rbac.check_permission(regular_user, "admin.access") is False
    
    # User should have their own permission
    assert await rbac.check_permission(regular_user, "user.read_own") is True


@pytest.mark.asyncio
async def test_check_permission_custom(rbac: RBAC, regular_user: User) -> None:
    """Test custom permissions."""
    regular_user.custom_permissions = ["custom.permission"]
    
    assert await rbac.check_permission(regular_user, "custom.permission") is True
    assert await rbac.check_permission(regular_user, "other.permission") is False


@pytest.mark.asyncio
async def test_check_permission_inactive_user(rbac: RBAC, admin_user: User) -> None:
    """Test that inactive users don't have permissions."""
    admin_user.is_active = False
    
    assert await rbac.check_permission(admin_user, "user.write") is False


@pytest.mark.asyncio
async def test_check_role(rbac: RBAC, admin_user: User, regular_user: User) -> None:
    """Test checking user roles."""
    assert await rbac.check_role(admin_user, UserRole.ADMIN) is True
    assert await rbac.check_role(admin_user, UserRole.USER) is False
    
    assert await rbac.check_role(regular_user, UserRole.USER) is True
    assert await rbac.check_role(regular_user, UserRole.ADMIN) is False


@pytest.mark.asyncio
async def test_check_any_permission(rbac: RBAC, moderator_user: User) -> None:
    """Test checking any permission."""
    # Moderator has user.read but not admin.access
    assert await rbac.check_any_permission(
        moderator_user,
        ["admin.access", "user.read"],
    ) is True
    
    assert await rbac.check_any_permission(
        moderator_user,
        ["admin.access", "module.install"],
    ) is False


@pytest.mark.asyncio
async def test_check_any_permission_super_admin(rbac: RBAC, super_admin_user: User) -> None:
    """Test super admin has any permission."""
    assert await rbac.check_any_permission(
        super_admin_user,
        ["any.permission", "other.permission"],
    ) is True


@pytest.mark.asyncio
async def test_has_wildcard(rbac: RBAC, super_admin_user: User, admin_user: User) -> None:
    """Test wildcard permission check."""
    assert rbac.has_wildcard(super_admin_user) is True
    assert rbac.has_wildcard(admin_user) is False

