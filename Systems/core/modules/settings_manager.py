"""
Settings manager for module settings.
"""

from typing import Any

from Systems.core.database.models.user import User
from Systems.core.database.repositories.settings_repository import SettingsRepository
from Systems.core.logger import get_logger
from Systems.core.modules.manifest import ModuleManifest

logger = get_logger(__name__)


class SettingsManager:
    """
    Settings manager for module settings.
    
    Provides type-safe access to module settings with validation.
    
    Example:
        ```python
        manager = SettingsManager(settings_repo)
        value = await manager.get_user_setting("my_module", user_id, "key")
        await manager.set_admin_setting("my_module", "key", "value")
        ```
    """
    
    def __init__(self, settings_repo: SettingsRepository) -> None:
        """
        Initialize settings manager.
        
        Args:
            settings_repo: Settings repository instance
        """
        self.settings_repo = settings_repo
        logger.debug("SettingsManager initialized")
    
    async def get_user_setting(
        self,
        module_name: str,
        user_id: int,
        key: str,
        default: Any = None,
    ) -> Any:
        """
        Get user-specific setting.
        
        Args:
            module_name: Module name
            user_id: User ID
            key: Setting key
            default: Default value if not found
            
        Returns:
            Setting value or default
            
        Example:
            ```python
            value = await manager.get_user_setting("my_module", 123456, "theme")
            ```
        """
        logger.debug(f"Getting user setting: {module_name}.{key} for user {user_id}")
        
        setting = await self.settings_repo.get_user_setting(module_name, user_id, key)
        
        if setting:
            return setting.setting_value
        return default
    
    async def set_user_setting(
        self,
        module_name: str,
        user_id: int,
        key: str,
        value: Any,
        manifest: ModuleManifest | None = None,
    ) -> None:
        """
        Set user-specific setting.
        
        Validates value type if manifest is provided.
        
        Args:
            module_name: Module name
            user_id: User ID
            key: Setting key
            value: Setting value
            manifest: Module manifest for validation (optional)
            
        Raises:
            ValueError: If value doesn't match schema
            
        Example:
            ```python
            await manager.set_user_setting("my_module", 123456, "theme", "dark")
            ```
        """
        logger.info(f"Setting user setting: {module_name}.{key} for user {user_id}")
        
        # Validate if manifest provided
        if manifest:
            self._validate_setting(key, value, manifest)
        
        await self.settings_repo.set_user_setting(module_name, user_id, key, value)
        await self.settings_repo.session.commit()
        
        logger.debug(f"User setting set: {module_name}.{key}")
    
    async def get_admin_setting(
        self,
        module_name: str,
        key: str,
        default: Any = None,
    ) -> Any:
        """
        Get admin-level setting.
        
        Args:
            module_name: Module name
            key: Setting key
            default: Default value if not found
            
        Returns:
            Setting value or default
            
        Example:
            ```python
            value = await manager.get_admin_setting("my_module", "max_users")
            ```
        """
        logger.debug(f"Getting admin setting: {module_name}.{key}")
        
        setting = await self.settings_repo.get_admin_setting(module_name, key)
        
        if setting:
            return setting.setting_value
        return default
    
    async def set_admin_setting(
        self,
        module_name: str,
        key: str,
        value: Any,
        manifest: ModuleManifest | None = None,
    ) -> None:
        """
        Set admin-level setting.
        
        Validates value type if manifest is provided.
        
        Args:
            module_name: Module name
            key: Setting key
            value: Setting value
            manifest: Module manifest for validation (optional)
            
        Raises:
            ValueError: If value doesn't match schema
            
        Example:
            ```python
            await manager.set_admin_setting("my_module", "max_users", 100)
            ```
        """
        logger.info(f"Setting admin setting: {module_name}.{key}")
        
        # Validate if manifest provided
        if manifest:
            self._validate_setting(key, value, manifest)
        
        await self.settings_repo.set_admin_setting(module_name, key, value)
        await self.settings_repo.session.commit()
        
        logger.debug(f"Admin setting set: {module_name}.{key}")
    
    def _validate_setting(
        self,
        key: str,
        value: Any,
        manifest: ModuleManifest,
    ) -> None:
        """
        Validate setting value against manifest schema.
        
        Args:
            key: Setting key
            value: Setting value
            manifest: Module manifest
            
        Raises:
            ValueError: If value doesn't match schema
        """
        if not manifest.settings:
            return
        
        if key not in manifest.settings:
            logger.warning(f"Setting {key} not defined in manifest")
            return
        
        schema = manifest.settings[key]
        expected_type = schema.get("type", "string")
        
        # Basic type validation
        type_map = {
            "string": str,
            "integer": int,
            "float": float,
            "boolean": bool,
            "array": list,
            "object": dict,
        }
        
        expected_python_type = type_map.get(expected_type)
        
        if expected_python_type:
            if not isinstance(value, expected_python_type):
                raise ValueError(
                    f"Setting {key} expects {expected_type}, got {type(value).__name__}"
                )
        
        # Additional validation (min/max for numbers, etc.)
        if expected_type in ("integer", "float"):
            if "min" in schema and value < schema["min"]:
                raise ValueError(f"Setting {key} value {value} is below minimum {schema['min']}")
            if "max" in schema and value > schema["max"]:
                raise ValueError(f"Setting {key} value {value} is above maximum {schema['max']}")
        
        logger.debug(f"Setting {key} validated successfully")

