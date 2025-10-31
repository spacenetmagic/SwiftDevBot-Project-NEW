"""
RBAC (Role-Based Access Control) system.
"""

from typing import TYPE_CHECKING

from Systems.core.logger import get_logger

if TYPE_CHECKING:
    from Systems.core.database.models.user import User

logger = get_logger(__name__)


# Role-based permissions mapping
ROLE_PERMISSIONS: dict[str, list[str]] = {
    "super_admin": [
        "*",  # Wildcard - all permissions
    ],
    "admin": [
        "user.read",
        "user.write",
        "user.delete",
        "module.read",
        "module.write",
        "module.enable",
        "module.disable",
        "module.install",
        "module.uninstall",
        "settings.read",
        "settings.write",
        "admin.access",
    ],
    "moderator": [
        "user.read",
        "content.moderate",
    ],
    "user": [
        "user.read_own",
    ],
}


class RBAC:
    """
    Role-Based Access Control system.
    
    Provides methods for checking user permissions and roles.
    Supports role-based permissions and custom user permissions.
    
    Example:
        ```python
        rbac = RBAC()
        
        # Check permission
        if await rbac.check_permission(user, "user.write"):
            # User can write
            pass
        
        # Check role
        if await rbac.check_role(user, UserRole.ADMIN):
            # User is admin
            pass
        ```
    """
    
    def __init__(self) -> None:
        """Initialize RBAC system."""
        logger.debug("RBAC initialized")
    
    def get_role_permissions(self, role: "UserRole") -> list[str]:
        """
        Get permissions for a role.
        
        Args:
            role: UserRole enum value
            
        Returns:
            List of permission strings
            
        Example:
            ```python
            permissions = rbac.get_role_permissions(UserRole.ADMIN)
            # Returns: ["user.read", "user.write", ...]
            ```
        """
        role_name = role.value if hasattr(role, "value") else str(role)
        permissions = ROLE_PERMISSIONS.get(role_name, [])
        
        logger.debug(f"Role {role_name} has {len(permissions)} permissions")
        return permissions.copy()  # Return copy to prevent modification
    
    async def check_permission(self, user: "User", permission: str) -> bool:
        """
        Check if user has a specific permission.
        
        Checks both role permissions and custom permissions.
        Super admin with "*" permission has access to everything.
        
        Args:
            user: User object
            permission: Permission string to check
            
        Returns:
            True if user has permission, False otherwise
            
        Example:
            ```python
            can_write = await rbac.check_permission(user, "user.write")
            if can_write:
                # Allow operation
                pass
            ```
        """
        if not user or not user.is_active:
            logger.debug(f"Permission check failed: user inactive or None")
            return False
        
        # Get role permissions
        role_perms = self.get_role_permissions(user.role)
        
        # Check for wildcard (super_admin)
        if "*" in role_perms:
            logger.debug(f"User {user.telegram_id} has wildcard permission")
            return True
        
        # Check role permissions
        if permission in role_perms:
            logger.debug(f"User {user.telegram_id} has permission '{permission}' via role")
            return True
        
        # Check custom permissions
        custom_perms = user.custom_permissions or []
        if permission in custom_perms:
            logger.debug(f"User {user.telegram_id} has permission '{permission}' via custom")
            return True
        
        logger.debug(f"User {user.telegram_id} does NOT have permission '{permission}'")
        return False
    
    async def check_role(self, user: "User", role: "UserRole") -> bool:
        """
        Check if user has a specific role.
        
        Args:
            user: User object
            role: UserRole to check
            
        Returns:
            True if user has the role, False otherwise
            
        Example:
            ```python
            is_admin = await rbac.check_role(user, UserRole.ADMIN)
            if is_admin:
                # User is admin
                pass
            ```
        """
        if not user or not user.is_active:
            return False
        
        user_role = user.role
        role_value = role.value if hasattr(role, "value") else role
        
        result = user_role.value == role_value if hasattr(user_role, "value") else user_role == role
        
        logger.debug(f"Role check: user {user.telegram_id} role={user_role.value} == {role_value} = {result}")
        return result
    
    async def check_any_permission(self, user: "User", permissions: list[str]) -> bool:
        """
        Check if user has any of the specified permissions.
        
        Args:
            user: User object
            permissions: List of permission strings to check
            
        Returns:
            True if user has at least one permission, False otherwise
            
        Example:
            ```python
            has_access = await rbac.check_any_permission(
                user,
                ["admin.access", "moderator.access"],
            )
            if has_access:
                # User has at least one permission
                pass
            ```
        """
        if not user or not user.is_active:
            return False
        
        for permission in permissions:
            if await self.check_permission(user, permission):
                logger.debug(f"User {user.telegram_id} has permission '{permission}'")
                return True
        
        logger.debug(f"User {user.telegram_id} does NOT have any of: {permissions}")
        return False
    
    def has_wildcard(self, user: "User") -> bool:
        """
        Check if user has wildcard permission (super_admin).
        
        Args:
            user: User object
            
        Returns:
            True if user has wildcard permission
        """
        if not user or not user.is_active:
            return False
        
        role_perms = self.get_role_permissions(user.role)
        return "*" in role_perms

