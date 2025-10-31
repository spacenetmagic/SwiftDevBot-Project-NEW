"""
Base module class for SwiftDevBot modules.
"""

from abc import ABC, abstractmethod
from typing import Any

from aiogram import Router

from Systems.core.database.repositories.settings_repository import SettingsRepository
from Systems.core.logger import get_logger
from Systems.core.modules.manifest import ModuleManifest


logger = get_logger(__name__)


class BaseModule(ABC):
    """
    Base class for all SwiftDevBot modules.
    
    Modules should inherit from this class and implement required methods.
    
    Example:
        ```python
        from Systems.core.modules import BaseModule
        
        class MyModule(BaseModule):
            async def on_load(self) -> None:
                self.logger.info("Module loaded")
                
            async def on_unload(self) -> None:
                self.logger.info("Module unloaded")
        ```
    """
    
    def __init__(
        self,
        manifest: ModuleManifest,
        settings_repo: SettingsRepository | None = None,
    ) -> None:
        """
        Initialize module.
        
        Args:
            manifest: Module manifest
            settings_repo: Settings repository (optional)
        """
        self.manifest = manifest
        self.settings_repo = settings_repo
        self.router = Router(name=f"module_{manifest.name}")
        self.enabled = False
        self.logger = get_logger(f"module.{manifest.name}")
        
        logger.debug(f"Module initialized: {manifest.name}")
    
    @property
    def name(self) -> str:
        """Get module name."""
        return self.manifest.name
    
    @property
    def version(self) -> str:
        """Get module version."""
        return self.manifest.version
    
    @abstractmethod
    async def on_load(self) -> None:
        """
        Called when module is loaded.
        
        Use this to initialize module resources, register handlers, etc.
        """
        pass
    
    @abstractmethod
    async def on_unload(self) -> None:
        """
        Called when module is unloaded.
        
        Use this to cleanup resources, stop background tasks, etc.
        """
        pass
    
    async def on_enable(self) -> None:
        """
        Called when module is enabled.
        
        Override if needed. Default implementation does nothing.
        """
        self.logger.debug(f"Module enabled: {self.name}")
    
    async def on_disable(self) -> None:
        """
        Called when module is disabled.
        
        Override if needed. Default implementation does nothing.
        """
        self.logger.debug(f"Module disabled: {self.name}")
    
    async def get_setting(
        self,
        key: str,
        user_id: int | None = None,
        default: Any = None,
    ) -> Any:
        """
        Get module setting value.
        
        Args:
            key: Setting key
            user_id: User ID for user settings (None for admin settings)
            default: Default value if setting not found
            
        Returns:
            Setting value or default
        """
        if not self.settings_repo:
            return default
        
        try:
            if user_id is not None:
                setting = await self.settings_repo.get_user_setting(
                    self.name,
                    user_id,
                    key,
                )
            else:
                setting = await self.settings_repo.get_admin_setting(self.name, key)
            
            if setting:
                return setting.setting_value
            return default
            
        except Exception as e:
            self.logger.error(f"Failed to get setting {key}: {e}")
            return default
    
    async def set_setting(
        self,
        key: str,
        value: Any,
        user_id: int | None = None,
    ) -> None:
        """
        Set module setting value.
        
        Args:
            key: Setting key
            value: Setting value
            user_id: User ID for user settings (None for admin settings)
        """
        if not self.settings_repo:
            self.logger.warning("Settings repository not available")
            return
        
        try:
            if user_id is not None:
                await self.settings_repo.set_user_setting(
                    self.name,
                    user_id,
                    key,
                    value,
                )
            else:
                await self.settings_repo.set_admin_setting(self.name, key, value)
            
            self.logger.debug(f"Setting {key} set for module {self.name}")
            
        except Exception as e:
            self.logger.error(f"Failed to set setting {key}: {e}")

