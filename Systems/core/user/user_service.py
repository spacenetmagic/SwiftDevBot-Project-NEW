"""
User service for managing users and their permissions.
"""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from Systems.core.database.models.user import User, UserRole
from Systems.core.database.repositories.audit_repository import AuditRepository
from Systems.core.database.repositories.user_repository import UserRepository
from Systems.core.logger import get_logger


logger = get_logger(__name__)


class UserService:
    """
    Service for user management operations.
    
    Provides high-level methods for user CRUD operations and permission management.
    All operations are logged to audit log.
    
    Example:
        ```python
        async with get_db() as session:
            user_service = UserService(session)
            user = await user_service.get_user(123456789)
            await user_service.change_user_role(123456789, UserRole.ADMIN)
        ```
    """
    
    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize user service.
        
        Args:
            session: Database session
        """
        self.session = session
        self.user_repo = UserRepository(session)
        self.audit_repo = AuditRepository(session)
        logger.debug("UserService initialized")
    
    async def get_user(self, telegram_id: int) -> User | None:
        """
        Get user by Telegram ID.
        
        Args:
            telegram_id: Telegram user ID
            
        Returns:
            User object or None if not found
            
        Example:
            ```python
            user = await user_service.get_user(123456789)
            if user:
                print(f"Found user: {user.username}")
            ```
        """
        logger.debug(f"Getting user: {telegram_id}")
        user = await self.user_repo.get_by_id(telegram_id)
        
        if user:
            logger.debug(f"User found: {telegram_id}")
        else:
            logger.debug(f"User not found: {telegram_id}")
        
        return user
    
    async def create_user(
        self,
        telegram_id: int,
        data: dict[str, Any],
        created_by: int | None = None,
    ) -> User:
        """
        Create a new user.
        
        Args:
            telegram_id: Telegram user ID
            data: User data dictionary
            created_by: ID of user who created this user (for audit)
            
        Returns:
            Created User object
            
        Raises:
            ValueError: If user already exists
            
        Example:
            ```python
            user = await user_service.create_user(
                123456789,
                {
                    "username": "newuser",
                    "first_name": "New",
                    "role": UserRole.USER,
                },
                created_by=999999999,
            )
            ```
        """
        logger.info(f"Creating user: {telegram_id}")
        
        # Check if user already exists
        existing = await self.get_user(telegram_id)
        if existing:
            raise ValueError(f"User with telegram_id {telegram_id} already exists")
        
        # Ensure telegram_id is set
        data["telegram_id"] = telegram_id
        
        user = await self.user_repo.create(data)
        await self.session.commit()
        
        # Log creation
        await self.audit_repo.log(
            user_id=created_by or telegram_id,
            action="user.create",
            resource=f"user:{telegram_id}",
            new_value={
                "telegram_id": telegram_id,
                "username": user.username,
                "role": user.role.value,
            },
            success=True,
        )
        await self.session.commit()
        
        logger.info(f"User created successfully: {telegram_id}")
        return user
    
    async def update_user(
        self,
        telegram_id: int,
        data: dict[str, Any],
        updated_by: int | None = None,
    ) -> User | None:
        """
        Update user information.
        
        Args:
            telegram_id: Telegram user ID
            data: Dictionary with fields to update
            updated_by: ID of user who updated (for audit)
            
        Returns:
            Updated User object or None if not found
            
        Example:
            ```python
            user = await user_service.update_user(
                123456789,
                {"username": "newusername", "first_name": "Updated"},
                updated_by=999999999,
            )
            ```
        """
        logger.info(f"Updating user: {telegram_id}")
        
        # Get current user state
        current_user = await self.get_user(telegram_id)
        if not current_user:
            logger.warning(f"User not found for update: {telegram_id}")
            return None
        
        old_value = {
            "username": current_user.username,
            "first_name": current_user.first_name,
            "last_name": current_user.last_name,
            "role": current_user.role.value,
            "is_active": current_user.is_active,
        }
        
        # Update user
        user = await self.user_repo.update(telegram_id, data)
        await self.session.commit()
        
        if user:
            # Log update
            new_value = {
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role.value,
                "is_active": user.is_active,
            }
            
            await self.audit_repo.log(
                user_id=updated_by or telegram_id,
                action="user.update",
                resource=f"user:{telegram_id}",
                old_value=old_value,
                new_value=new_value,
                success=True,
            )
            await self.session.commit()
            
            logger.info(f"User updated successfully: {telegram_id}")
        
        return user
    
    async def get_or_create(
        self,
        telegram_id: int,
        defaults: dict[str, Any] | None = None,
    ) -> tuple[User, bool]:
        """
        Get existing user or create new one.
        
        Args:
            telegram_id: Telegram user ID
            defaults: Default values for new user creation
            
        Returns:
            Tuple of (User object, created: bool)
            
        Example:
            ```python
            user, created = await user_service.get_or_create(
                123456789,
                defaults={"username": "newuser", "first_name": "New"},
            )
            if created:
                print("New user created")
            ```
        """
        user = await self.get_user(telegram_id)
        
        if user:
            logger.debug(f"User already exists: {telegram_id}")
            return user, False
        
        # Create new user
        if defaults is None:
            defaults = {}
        
        defaults.setdefault("role", UserRole.USER)
        
        user = await self.create_user(telegram_id, defaults)
        logger.info(f"New user created via get_or_create: {telegram_id}")
        
        return user, True
    
    async def change_user_role(
        self,
        telegram_id: int,
        new_role: UserRole,
        changed_by: int | None = None,
    ) -> User | None:
        """
        Change user role.
        
        Args:
            telegram_id: Telegram user ID
            new_role: New role to assign
            changed_by: ID of user who changed the role (for audit)
            
        Returns:
            Updated User object or None if not found
            
        Raises:
            ValueError: If trying to change super_admin role without proper permissions
            
        Example:
            ```python
            user = await user_service.change_user_role(
                123456789,
                UserRole.ADMIN,
                changed_by=999999999,
            )
            ```
        """
        logger.info(f"Changing user role: {telegram_id} -> {new_role.value}")
        
        user = await self.get_user(telegram_id)
        if not user:
            logger.warning(f"User not found for role change: {telegram_id}")
            return None
        
        old_role = user.role
        
        # Prevent changing super_admin role
        if old_role == UserRole.SUPER_ADMIN and new_role != UserRole.SUPER_ADMIN:
            raise ValueError("Cannot change super_admin role")
        
        # Update role
        user = await self.update_user(
            telegram_id,
            {"role": new_role},
            updated_by=changed_by,
        )
        
        if user:
            # Log role change
            await self.audit_repo.log(
                user_id=changed_by or telegram_id,
                action="user.role_change",
                resource=f"user:{telegram_id}",
                old_value={"role": old_role.value},
                new_value={"role": new_role.value},
                success=True,
            )
            await self.session.commit()
            
            logger.info(f"User role changed: {telegram_id} {old_role.value} -> {new_role.value}")
        
        return user
    
    async def grant_permission(
        self,
        telegram_id: int,
        permission: str,
        granted_by: int | None = None,
    ) -> User | None:
        """
        Grant custom permission to user.
        
        Args:
            telegram_id: Telegram user ID
            permission: Permission string to grant
            granted_by: ID of user who granted permission (for audit)
            
        Returns:
            Updated User object or None if not found
            
        Example:
            ```python
            user = await user_service.grant_permission(
                123456789,
                "special.permission",
                granted_by=999999999,
            )
            ```
        """
        logger.info(f"Granting permission '{permission}' to user: {telegram_id}")
        
        user = await self.get_user(telegram_id)
        if not user:
            logger.warning(f"User not found for permission grant: {telegram_id}")
            return None
        
        # Get current permissions
        current_permissions = list(user.custom_permissions or [])
        
        # Add permission if not already present
        if permission not in current_permissions:
            current_permissions.append(permission)
            
            user = await self.update_user(
                telegram_id,
                {"custom_permissions": current_permissions},
                updated_by=granted_by,
            )
            
            if user:
                # Log permission grant
                await self.audit_repo.log(
                    user_id=granted_by or telegram_id,
                    action="user.permission.grant",
                    resource=f"user:{telegram_id}",
                    old_value={"permissions": list(user.custom_permissions or [])},
                    new_value={"permissions": current_permissions},
                    success=True,
                )
                await self.session.commit()
                
                logger.info(f"Permission '{permission}' granted to user: {telegram_id}")
        else:
            logger.debug(f"Permission '{permission}' already granted to user: {telegram_id}")
        
        return user
    
    async def revoke_permission(
        self,
        telegram_id: int,
        permission: str,
        revoked_by: int | None = None,
    ) -> User | None:
        """
        Revoke custom permission from user.
        
        Args:
            telegram_id: Telegram user ID
            permission: Permission string to revoke
            revoked_by: ID of user who revoked permission (for audit)
            
        Returns:
            Updated User object or None if not found
            
        Example:
            ```python
            user = await user_service.revoke_permission(
                123456789,
                "special.permission",
                revoked_by=999999999,
            )
            ```
        """
        logger.info(f"Revoking permission '{permission}' from user: {telegram_id}")
        
        user = await self.get_user(telegram_id)
        if not user:
            logger.warning(f"User not found for permission revoke: {telegram_id}")
            return None
        
        # Get current permissions
        current_permissions = list(user.custom_permissions or [])
        
        # Remove permission if present
        if permission in current_permissions:
            current_permissions.remove(permission)
            
            user = await self.update_user(
                telegram_id,
                {"custom_permissions": current_permissions},
                updated_by=revoked_by,
            )
            
            if user:
                # Log permission revoke
                await self.audit_repo.log(
                    user_id=revoked_by or telegram_id,
                    action="user.permission.revoke",
                    resource=f"user:{telegram_id}",
                    old_value={"permissions": list(user.custom_permissions or [])},
                    new_value={"permissions": current_permissions},
                    success=True,
                )
                await self.session.commit()
                
                logger.info(f"Permission '{permission}' revoked from user: {telegram_id}")
        else:
            logger.debug(f"Permission '{permission}' not found for user: {telegram_id}")
        
        return user
    
    async def get_user_permissions(self, user: User) -> list[str]:
        """
        Get all permissions for a user.
        
        Includes role-based permissions and custom permissions.
        
        Args:
            user: User object
            
        Returns:
            List of permission strings
            
        Example:
            ```python
            permissions = await user_service.get_user_permissions(user)
            if "user.write" in permissions:
                print("User can write")
            ```
        """
        # Lazy import to avoid circular dependency
        from Systems.core.rbac.rbac import RBAC
        
        rbac = RBAC()
        
        # Get role permissions
        role_permissions = rbac.get_role_permissions(user.role)
        
        # Get custom permissions
        custom_permissions = list(user.custom_permissions or [])
        
        # Combine and deduplicate
        all_permissions = list(set(role_permissions + custom_permissions))
        
        logger.debug(f"User {user.telegram_id} has {len(all_permissions)} permissions")
        
        return all_permissions
    
    async def list_users(
        self,
        skip: int = 0,
        limit: int = 100,
        role: UserRole | None = None,
    ) -> list[User]:
        """
        List users with optional filtering by role.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            role: Optional role filter
            
        Returns:
            List of User objects
            
        Example:
            ```python
            # Get all users
            users = await user_service.list_users(skip=0, limit=50)
            
            # Get only admins
            admins = await user_service.list_users(role=UserRole.ADMIN)
            ```
        """
        logger.debug(f"Listing users: skip={skip}, limit={limit}, role={role}")
        
        if role:
            users = await self.user_repo.get_by_role(role)
            # Apply pagination manually
            users = users[skip:skip + limit]
        else:
            users = await self.user_repo.get_all(skip=skip, limit=limit)
        
        logger.debug(f"Found {len(users)} users")
        return users

