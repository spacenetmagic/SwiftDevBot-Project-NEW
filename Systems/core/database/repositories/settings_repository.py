"""
Settings repository for database operations.
"""

from typing import Any

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from Systems.core.database.models.module_settings import ModuleSetting, SettingLevel
from Systems.core.logger import get_logger


logger = get_logger(__name__)


class SettingsRepository:
    """
    Repository for ModuleSetting model operations.
    
    Provides methods for managing module settings at user and admin levels.
    """
    
    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize repository with database session.
        
        Args:
            session: Async database session
        """
        self.session = session
        logger.debug("SettingsRepository initialized")
    
    async def get_user_setting(
        self,
        module_name: str,
        user_id: int,
        key: str,
    ) -> ModuleSetting | None:
        """
        Get user-specific setting.
        
        Args:
            module_name: Name of the module
            user_id: User ID
            key: Setting key
            
        Returns:
            ModuleSetting instance or None if not found
        """
        logger.debug(f"Fetching user setting: module={module_name}, user={user_id}, key={key}")
        
        stmt = (
            select(ModuleSetting)
            .where(
                ModuleSetting.module_name == module_name,
                ModuleSetting.level == SettingLevel.USER_SETTING,
                ModuleSetting.user_id == user_id,
                ModuleSetting.setting_key == key,
            )
        )
        result = await self.session.execute(stmt)
        setting = result.scalar_one_or_none()
        
        return setting
    
    async def set_user_setting(
        self,
        module_name: str,
        user_id: int,
        key: str,
        value: Any,
    ) -> ModuleSetting:
        """
        Set user-specific setting (create or update).
        
        Args:
            module_name: Name of the module
            user_id: User ID
            key: Setting key
            value: Setting value
            
        Returns:
            Created or updated ModuleSetting instance
        """
        logger.info(f"Setting user setting: module={module_name}, user={user_id}, key={key}")
        
        # Try to get existing setting
        existing = await self.get_user_setting(module_name, user_id, key)
        
        if existing:
            existing.setting_value = value
            await self.session.flush()
            await self.session.refresh(existing)
            logger.debug(f"Updated existing user setting: {key}")
            return existing
        
        # Create new setting
        setting = ModuleSetting(
            module_name=module_name,
            level=SettingLevel.USER_SETTING,
            user_id=user_id,
            setting_key=key,
            setting_value=value,
        )
        self.session.add(setting)
        await self.session.flush()
        await self.session.refresh(setting)
        
        logger.info(f"Created new user setting: {key}")
        return setting
    
    async def get_admin_setting(
        self,
        module_name: str,
        key: str,
    ) -> ModuleSetting | None:
        """
        Get admin-level setting.
        
        Args:
            module_name: Name of the module
            key: Setting key
            
        Returns:
            ModuleSetting instance or None if not found
        """
        logger.debug(f"Fetching admin setting: module={module_name}, key={key}")
        
        stmt = (
            select(ModuleSetting)
            .where(
                ModuleSetting.module_name == module_name,
                ModuleSetting.level == SettingLevel.ADMIN_SETTING,
                ModuleSetting.user_id.is_(None),
                ModuleSetting.setting_key == key,
            )
        )
        result = await self.session.execute(stmt)
        setting = result.scalar_one_or_none()
        
        return setting
    
    async def set_admin_setting(
        self,
        module_name: str,
        key: str,
        value: Any,
    ) -> ModuleSetting:
        """
        Set admin-level setting (create or update).
        
        Args:
            module_name: Name of the module
            key: Setting key
            value: Setting value
            
        Returns:
            Created or updated ModuleSetting instance
        """
        logger.info(f"Setting admin setting: module={module_name}, key={key}")
        
        # Try to get existing setting
        existing = await self.get_admin_setting(module_name, key)
        
        if existing:
            existing.setting_value = value
            await self.session.flush()
            await self.session.refresh(existing)
            logger.debug(f"Updated existing admin setting: {key}")
            return existing
        
        # Create new setting
        setting = ModuleSetting(
            module_name=module_name,
            level=SettingLevel.ADMIN_SETTING,
            user_id=None,
            setting_key=key,
            setting_value=value,
        )
        self.session.add(setting)
        await self.session.flush()
        await self.session.refresh(setting)
        
        logger.info(f"Created new admin setting: {key}")
        return setting
    
    async def get_all_user_settings(
        self,
        module_name: str,
        user_id: int,
    ) -> list[ModuleSetting]:
        """
        Get all user settings for a module.
        
        Args:
            module_name: Name of the module
            user_id: User ID
            
        Returns:
            List of ModuleSetting instances
        """
        logger.debug(f"Fetching all user settings: module={module_name}, user={user_id}")
        
        stmt = (
            select(ModuleSetting)
            .where(
                ModuleSetting.module_name == module_name,
                ModuleSetting.level == SettingLevel.USER_SETTING,
                ModuleSetting.user_id == user_id,
            )
            .order_by(ModuleSetting.setting_key)
        )
        result = await self.session.execute(stmt)
        settings = result.scalars().all()
        
        logger.debug(f"Found {len(settings)} user settings")
        return list(settings)
    
    async def delete_setting(
        self,
        module_name: str,
        key: str,
        user_id: int | None = None,
    ) -> bool:
        """
        Delete a setting.
        
        Args:
            module_name: Name of the module
            key: Setting key
            user_id: User ID for user settings (None for admin settings)
            
        Returns:
            True if deleted, False if not found
        """
        logger.info(f"Deleting setting: module={module_name}, key={key}, user={user_id}")
        
        if user_id is not None:
            # User setting
            setting = await self.get_user_setting(module_name, user_id, key)
            level = SettingLevel.USER_SETTING
        else:
            # Admin setting
            setting = await self.get_admin_setting(module_name, key)
            level = SettingLevel.ADMIN_SETTING
        
        if not setting:
            logger.warning(f"Setting not found for deletion: {key}")
            return False
        
        await self.session.delete(setting)
        await self.session.flush()
        
        logger.info(f"Setting deleted successfully: {key}")
        return True

