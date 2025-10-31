"""
RBAC middleware for aiogram bot.
"""

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from aiogram.types.user import User as TelegramUser

from Systems.core.logger import get_logger
from Systems.core.rbac.rbac import RBAC

logger = get_logger(__name__)


class RBACMiddleware(BaseMiddleware):
    """
    RBAC middleware for aiogram handlers.
    
    Checks user permissions before executing handler.
    
    Usage:
        ```python
        from Systems.core.rbac.middleware import RBACMiddleware
        
        # Register middleware
        dp.message.middleware(RBACMiddleware(required_permission="user.write"))
        
        # Or for specific handlers
        @router.message(Command("admin"))
        async def admin_command(message: Message):
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
            required_role: Required role name
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
        
        Checks permissions before executing handler.
        
        Args:
            handler: Handler function
            event: Telegram event
            data: Handler data
            
        Returns:
            Handler result or raises exception if permission denied
        """
        # Get Telegram user from event
        telegram_user: TelegramUser | None = None
        
        if hasattr(event, "from_user"):
            telegram_user = event.from_user
        
        if not telegram_user:
            logger.warning("RBACMiddleware: No user found in event")
            # Let handler decide what to do
            return await handler(event, data)
        
        # Get user from database
        from sqlalchemy.ext.asyncio import AsyncSession
        
        session: AsyncSession | None = data.get("session")
        if not session:
            logger.warning("RBACMiddleware: No database session found")
            return await handler(event, data)
        
        from Systems.core.database.repositories.user_repository import UserRepository
        
        user_repo = UserRepository(session)
        user = await user_repo.get_by_id(telegram_user.id)
        
        if not user:
            logger.warning(f"RBACMiddleware: User {telegram_user.id} not found in database")
            # Create user or deny access - let handler decide
            return await handler(event, data)
        
        # Check permissions
        if self.required_role:
            from Systems.core.database.models.user import UserRole
            
            role_enum = UserRole(self.required_role) if isinstance(self.required_role, str) else self.required_role
            has_access = await self.rbac.check_role(user, role_enum)
            
            if not has_access:
                logger.warning(
                    f"RBACMiddleware: Access denied for user {user.telegram_id}: "
                    f"required role {self.required_role}",
                )
                # Optionally send message to user
                if hasattr(event, "answer"):
                    await event.answer("❌ У вас нет доступа к этой команде.")
                return None
        
        if self.required_permission:
            has_access = await self.rbac.check_permission(user, self.required_permission)
            
            if not has_access:
                logger.warning(
                    f"RBACMiddleware: Access denied for user {user.telegram_id}: "
                    f"required permission {self.required_permission}",
                )
                if hasattr(event, "answer"):
                    await event.answer("❌ У вас нет прав для выполнения этой команды.")
                return None
        
        if self.required_permissions:
            has_access = await self.rbac.check_any_permission(user, self.required_permissions)
            
            if not has_access:
                logger.warning(
                    f"RBACMiddleware: Access denied for user {user.telegram_id}: "
                    f"required any permission from {self.required_permissions}",
                )
                if hasattr(event, "answer"):
                    await event.answer("❌ У вас нет прав для выполнения этой команды.")
                return None
        
        # Permission granted, execute handler
        logger.debug(f"RBACMiddleware: Access granted for user {user.telegram_id}")
        return await handler(event, data)

