"""
User repository for database operations.
"""

from typing import Any

from sqlalchemy import select, func as sql_func
from sqlalchemy.ext.asyncio import AsyncSession

from Systems.core.database.models.user import User, UserRole
from Systems.core.logger import get_logger


logger = get_logger(__name__)


class UserRepository:
    """
    Repository for User model operations.
    
    Provides methods for CRUD operations and queries on User entities.
    """
    
    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize repository with database session.
        
        Args:
            session: Async database session
        """
        self.session = session
        logger.debug("UserRepository initialized")
    
    async def get_by_id(self, telegram_id: int) -> User | None:
        """
        Get user by Telegram ID.
        
        Args:
            telegram_id: Telegram user ID
            
        Returns:
            User instance or None if not found
        """
        logger.debug(f"Fetching user by ID: {telegram_id}")
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()
        
        if user:
            logger.debug(f"User found: {telegram_id}")
        else:
            logger.debug(f"User not found: {telegram_id}")
        
        return user
    
    async def create(self, data: dict[str, Any]) -> User:
        """
        Create a new user.
        
        Args:
            data: User data dictionary
            
        Returns:
            Created User instance
            
        Raises:
            ValueError: If user already exists
        """
        telegram_id = data.get("telegram_id")
        logger.info(f"Creating user: {telegram_id}")
        
        # Check if user already exists
        existing = await self.get_by_id(telegram_id)
        if existing:
            raise ValueError(f"User with telegram_id {telegram_id} already exists")
        
        user = User(**data)
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        
        logger.info(f"User created successfully: {telegram_id}")
        return user
    
    async def update(self, telegram_id: int, data: dict[str, Any]) -> User | None:
        """
        Update user by Telegram ID.
        
        Args:
            telegram_id: Telegram user ID
            data: Dictionary with fields to update
            
        Returns:
            Updated User instance or None if not found
        """
        logger.info(f"Updating user: {telegram_id}")
        
        user = await self.get_by_id(telegram_id)
        if not user:
            logger.warning(f"User not found for update: {telegram_id}")
            return None
        
        # Update fields
        for key, value in data.items():
            if hasattr(user, key):
                setattr(user, key, value)
        
        await self.session.flush()
        await self.session.refresh(user)
        
        logger.info(f"User updated successfully: {telegram_id}")
        return user
    
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> list[User]:
        """
        Get all users with pagination.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of User instances
        """
        logger.debug(f"Fetching users: skip={skip}, limit={limit}")
        
        stmt = (
            select(User)
            .order_by(User.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        users = result.scalars().all()
        
        logger.debug(f"Found {len(users)} users")
        return list(users)
    
    async def delete(self, telegram_id: int) -> bool:
        """
        Delete user by Telegram ID.
        
        Args:
            telegram_id: Telegram user ID
            
        Returns:
            True if deleted, False if not found
        """
        logger.info(f"Deleting user: {telegram_id}")
        
        user = await self.get_by_id(telegram_id)
        if not user:
            logger.warning(f"User not found for deletion: {telegram_id}")
            return False
        
        await self.session.delete(user)
        await self.session.flush()
        
        logger.info(f"User deleted successfully: {telegram_id}")
        return True
    
    async def get_by_role(self, role: UserRole) -> list[User]:
        """
        Get all users with specific role.
        
        Args:
            role: User role to filter by
            
        Returns:
            List of User instances with the specified role
        """
        logger.debug(f"Fetching users by role: {role}")
        
        stmt = select(User).where(User.role == role).order_by(User.created_at.desc())
        result = await self.session.execute(stmt)
        users = result.scalars().all()
        
        logger.debug(f"Found {len(users)} users with role {role}")
        return list(users)
    
    async def count_all(self) -> int:
        """
        Get total count of all users.
        
        Returns:
            Total number of users
        """
        logger.debug("Counting all users")
        
        stmt = select(sql_func.count(User.telegram_id))
        result = await self.session.execute(stmt)
        count = result.scalar_one()
        
        logger.debug(f"Total users: {count}")
        return count or 0

