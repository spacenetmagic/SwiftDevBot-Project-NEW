"""
Module manager for managing module lifecycle and integration.
"""

from typing import Any

from aiogram import Dispatcher

from Systems.core.database import get_session_factory
from Systems.core.database.repositories.settings_repository import SettingsRepository
from Systems.core.logger import get_logger
from Systems.core.modules.base_module import BaseModule
from Systems.core.modules.loader import ModuleLoader

logger = get_logger(__name__)


class ModuleManager:
    """
    Module manager for SwiftDevBot.
    
    Manages module lifecycle, integration with dispatcher, and user access.
    
    Example:
        ```python
        loader = ModuleLoader(Path("Modules"))
        manager = ModuleManager(loader, dp, db_session)
        await manager.initialize()
        await manager.load_all_modules()
        ```
    """
    
    def __init__(
        self,
        loader: ModuleLoader,
        dispatcher: Dispatcher | None = None,
        db_session: Any = None,
    ) -> None:
        """
        Initialize module manager.
        
        Args:
            loader: Module loader instance
            dispatcher: Aiogram dispatcher (optional)
            db_session: Database session (optional)
        """
        self.loader = loader
        self.dispatcher = dispatcher
        self.db_session = db_session
        self._session_factory = None
        
        # Initialize settings repository if db_session provided
        self.settings_repo = None
        if db_session:
            self.settings_repo = SettingsRepository(db_session)
        
        logger.info("ModuleManager initialized")
    
    @property
    def session_factory(self):
        """Lazy initialization of session factory."""
        if self._session_factory is None:
            self._session_factory = get_session_factory()
        return self._session_factory
    
    async def initialize(self) -> None:
        """
        Initialize module manager.
        
        Discovers and loads all available modules.
        """
        logger.info("Initializing module manager...")
        
        modules = await self.loader.discover_modules()
        logger.info(f"Found {len(modules)} modules")
        
        # Load enabled modules (those with enabled_by_default=True)
        for module_name in modules:
            try:
                manifest = self.loader._module_manifests.get(module_name)
                if not manifest:
                    # Load manifest first
                    module_path = self.loader.modules_path / module_name
                    from Systems.core.modules.manifest import load_manifest
                    
                    manifest = load_manifest(module_path)
                    self.loader._module_manifests[module_name] = manifest
                
                if manifest.enabled_by_default:
                    await self.enable_module(module_name)
                    
            except Exception as e:
                logger.error(f"Failed to auto-enable module {module_name}: {e}")
        
        logger.info("Module manager initialized")
    
    async def load_all_modules(self) -> dict[str, BaseModule]:
        """
        Load all discovered modules.
        
        Returns:
            Dictionary of loaded modules
            
        Example:
            ```python
            modules = await manager.load_all_modules()
            ```
        """
        logger.info("Loading all modules...")
        
        modules = await self.loader.discover_modules()
        loaded = {}
        
        for module_name in modules:
            try:
                module = await self.loader.load_module(module_name, self.db_session)
                loaded[module_name] = module
            except Exception as e:
                logger.error(f"Failed to load module {module_name}: {e}")
        
        logger.info(f"Loaded {len(loaded)} modules")
        return loaded
    
    async def get_available_modules(
        self,
        user: Any = None,
    ) -> list[BaseModule]:
        """
        Get available modules for a user.
        
        Filters modules based on user permissions.
        
        Args:
            user: User object (optional, for permission checking)
            
        Returns:
            List of available modules
        """
        loaded_modules = self.loader.get_loaded_modules()
        
        if not user:
            return list(loaded_modules.values())
        
        # Filter by permissions if needed
        available = []
        for module in loaded_modules.values():
            # TODO: Add permission checking based on manifest
            available.append(module)
        
        return available
    
    async def enable_module(self, module_name: str) -> BaseModule:
        """
        Enable a module.
        
        Loads module if not loaded, registers router, and calls on_enable.
        
        Args:
            module_name: Name of the module to enable
            
        Returns:
            Enabled BaseModule instance
            
        Example:
            ```python
            module = await manager.enable_module("my_module")
            ```
        """
        logger.info(f"Enabling module: {module_name}")
        
        # Get or load module
        module = self.loader.get_loaded_module(module_name)
        
        if not module:
            # Load module
            if self.db_session:
                module = await self.loader.load_module(module_name, self.db_session)
            else:
                async with self.session_factory() as session:
                    module = await self.loader.load_module(module_name, session)
        
        # Register router with dispatcher
        if self.dispatcher and module.router:
            self.dispatcher.include_router(module.router)
            logger.debug(f"Router registered for module: {module_name}")
        
        # Enable module
        module.enabled = True
        await module.on_enable()
        
        logger.info(f"Module enabled: {module_name}")
        return module
    
    async def disable_module(self, module_name: str) -> None:
        """
        Disable a module.
        
        Calls on_disable and removes router from dispatcher.
        
        Args:
            module_name: Name of the module to disable
            
        Example:
            ```python
            await manager.disable_module("my_module")
            ```
        """
        logger.info(f"Disabling module: {module_name}")
        
        module = self.loader.get_loaded_module(module_name)
        
        if not module:
            logger.warning(f"Module not loaded: {module_name}")
            return
        
        # Disable module
        module.enabled = False
        await module.on_disable()
        
        # Remove router from dispatcher (note: aiogram doesn't support removing routers easily)
        # We'll just mark it as disabled
        
        logger.info(f"Module disabled: {module_name}")
    
    async def reload_module(self, module_name: str) -> BaseModule:
        """
        Reload a module (hot reload).
        
        Args:
            module_name: Name of the module to reload
            
        Returns:
            Reloaded BaseModule instance
            
        Example:
            ```python
            module = await manager.reload_module("my_module")
            ```
        """
        logger.info(f"Reloading module: {module_name}")
        
        was_enabled = False
        module = self.loader.get_loaded_module(module_name)
        
        if module and module.enabled:
            was_enabled = True
            await self.disable_module(module_name)
        
        # Reload
        if self.db_session:
            module = await self.loader.reload_module(module_name, self.db_session)
        else:
            async with self.session_factory() as session:
                module = await self.loader.reload_module(module_name, session)
        
        # Re-enable if it was enabled
        if was_enabled:
            await self.enable_module(module_name)
        
        logger.info(f"Module reloaded: {module_name}")
        return module

