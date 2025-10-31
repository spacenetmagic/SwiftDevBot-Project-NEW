"""
RBAC decorators for FastAPI routes.
"""

from typing import Annotated, Any, Callable

from fastapi import Depends, HTTPException, status

from Systems.core.database.models.user import User, UserRole
from Systems.core.logger import get_logger
from Systems.core.rbac.rbac import RBAC
from Systems.web.auth.dependencies import get_current_user

logger = get_logger(__name__)

rbac = RBAC()


def require_role(
    roles: list[UserRole | str],
) -> Callable[[Annotated[User, Depends(get_current_user)]], User]:
    """
    FastAPI dependency to require specific role(s).
    
    Usage:
        ```python
        @app.get("/admin")
        async def admin_route(user: User = Depends(require_role([UserRole.ADMIN]))):
            return {"message": "Admin only"}
        
        # Multiple roles
        @app.get("/staff")
        async def staff_route(user: User = Depends(require_role([UserRole.ADMIN, UserRole.MODERATOR]))):
            return {"message": "Staff only"}
        ```
    
    Args:
        roles: List of allowed roles (UserRole enum or string)
        
    Returns:
        Dependency function that raises HTTPException if role doesn't match
    """
    role_values = [
        role.value if isinstance(role, UserRole) else role
        for role in roles
    ]
    
    async def check_role(
        user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        user_role = user.role.value if hasattr(user.role, "value") else str(user.role)
        
        if user_role not in role_values:
            logger.warning(
                f"Access denied for user {user.telegram_id}: "
                f"required roles {role_values}, got {user_role}",
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required role: {', '.join(role_values)}",
            )
        
        return user
    
    return check_role


def require_permission(
    permission: str,
) -> Callable[[Annotated[User, Depends(get_current_user)]], User]:
    """
    FastAPI dependency to require specific permission.
    
    Usage:
        ```python
        @app.post("/users")
        async def create_user(user: User = Depends(require_permission("user.write"))):
            return {"message": "User created"}
        ```
    
    Args:
        permission: Required permission string
        
    Returns:
        Dependency function that raises HTTPException if permission not granted
    """
    async def check_permission(
        user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        has_permission = await rbac.check_permission(user, permission)
        
        if not has_permission:
            logger.warning(
                f"Access denied for user {user.telegram_id}: "
                f"required permission '{permission}'",
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required permission: {permission}",
            )
        
        return user
    
    return check_permission


def require_any_permission(
    permissions: list[str],
) -> Callable[[Annotated[User, Depends(get_current_user)]], User]:
    """
    FastAPI dependency to require any of the specified permissions.
    
    Usage:
        ```python
        @app.get("/dashboard")
        async def dashboard(
            user: User = Depends(require_any_permission(["admin.access", "moderator.access"])),
        ):
            return {"dashboard": "data"}
        ```
    
    Args:
        permissions: List of permission strings (user needs at least one)
        
    Returns:
        Dependency function that raises HTTPException if no permission granted
    """
    async def check_any_permission(
        user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        has_permission = await rbac.check_any_permission(user, permissions)
        
        if not has_permission:
            logger.warning(
                f"Access denied for user {user.telegram_id}: "
                f"required any of: {permissions}",
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required any permission: {', '.join(permissions)}",
            )
        
        return user
    
    return check_any_permission

