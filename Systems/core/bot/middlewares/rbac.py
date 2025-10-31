"""
RBAC middleware for bot handlers.
"""

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from Systems.core.logger import get_logger
from Systems.core.rbac.rbac import RBAC

logger = get_logger(__name__)


class RBACMiddleware(BaseMiddleware):
    """
    RBAC middleware for aiogram handlers.
    
    Checks user permissions before executing handler.
    Must be used after AuthMiddleware.
    
    Usage:
        ```python
        # Global middleware
        dp.message.middleware(RBACMiddleware(required_permission="user.write"))
        
        # Or in handler decorator
        @router.message(Command("admin"))
        async def admin_command(message: Message, user: User):
            # This handler requires permission check
            pass
        ```
    """
    
    def __init__(
        self,
        required_permission: str | None = None,
        required_role: str | None = None,
        required_permissions: list[str] | None = None,
    ) -> None:
        """
        Initialize RBAC middleware.
        
        Args:
            required_permission: Single required permission
            required_role: Required role name (e.g., "admin")
            required_permissions: List of permissions (user needs any of them)
        """
        self.required_permission = required_permission
        self.required_role = required_role
        self.required_permissions = required_permissions
        self.rbac = RBAC()
        
        logger.debug(
            f"RBACMiddleware initialized: "
            f"permission={required_permission}, "
            f"role={required_role}, "
            f"permissions={required_permissions}",
        )
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        """
        Middleware call handler.
        
        Args:
            handler: Handler function
            event: Telegram event
            data: Handler data (should contain 'user' from AuthMiddleware)
            
        Returns:
            Handler result or None if access denied
        """
        # Get user from data (set by AuthMiddleware)
        from Systems.core.database.models.user import User
        
        user: User | None = data.get("user")
        
        if not user:
            logger.warning("RBACMiddleware: No user in data (AuthMiddleware should run first)")
            # Let handler decide what to do
            return await handler(event, data)
        
        # Check permissions
        has_access = True
        
        if self.required_role:
            from Systems.core.database.models.user import UserRole
            
            try:
                role_enum = (
                    UserRole(self.required_role)
                    if isinstance(self.required_role, str)
                    else self.required_role
                )
                has_access = await self.rbac.check_role(user, role_enum)
            except (ValueError, AttributeError) as e:
                logger.error(f"Invalid role check: {e}")
                has_access = False
            
            if not has_access:
                logger.warning(
                    f"RBACMiddleware: Access denied for user {user.telegram_id}: "
                    f"required role {self.required_role}",
                )
                if hasattr(event, "answer"):
                    await event.answer(
                        "❌ У вас нет доступа к этой команде.\n"
                        f"Требуется роль: {self.required_role}",
                    )
                return None
        
        if self.required_permission:
            has_access = await self.rbac.check_permission(user, self.required_permission)
            
            if not has_access:
                logger.warning(
                    f"RBACMiddleware: Access denied for user {user.telegram_id}: "
                    f"required permission {self.required_permission}",
                )
                if hasattr(event, "answer"):
                    await event.answer(
                        "❌ У вас нет прав для выполнения этой команды.\n"
                        f"Требуется право: {self.required_permission}",
                    )
                return None
        
        if self.required_permissions:
            has_access = await self.rbac.check_any_permission(user, self.required_permissions)
            
            if not has_access:
                logger.warning(
                    f"RBACMiddleware: Access denied for user {user.telegram_id}: "
                    f"required any permission from {self.required_permissions}",
                )
                if hasattr(event, "answer"):
                    await event.answer(
                        "❌ У вас нет прав для выполнения этой команды.",
                    )
                return None
        
        # Permission granted
        logger.debug(f"RBACMiddleware: Access granted for user {user.telegram_id}")
        return await handler(event, data)

