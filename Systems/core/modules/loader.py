"""
Module loader for discovering and loading modules.
"""

import importlib
import importlib.util
import sys
from pathlib import Path
from typing import Any

from Systems.core.logger import get_logger
from Systems.core.modules.base_module import BaseModule
from Systems.core.modules.manifest import ModuleManifest, load_manifest

logger = get_logger(__name__)


class ModuleLoader:
    """
    Module loader for discovering and loading SwiftDevBot modules.
    
    Handles module discovery, loading, unloading, and dependency checking.
    
    Example:
        ```python
        loader = ModuleLoader(Path("Modules"))
        modules = await loader.discover_modules()
        module = await loader.load_module("my_module")
        ```
    """
    
    def __init__(self, modules_path: Path) -> None:
        """
        Initialize module loader.
        
        Args:
            modules_path: Path to modules directory
        """
        self.modules_path = Path(modules_path)
        self.modules_path.mkdir(parents=True, exist_ok=True)
        
        self._loaded_modules: dict[str, BaseModule] = {}
        self._module_manifests: dict[str, ModuleManifest] = {}
        
        logger.info(f"ModuleLoader initialized: {self.modules_path}")
    
    async def discover_modules(self) -> list[str]:
        """
        Discover all available modules in modules directory.
        
        Returns:
            List of module names
            
        Example:
            ```python
            modules = await loader.discover_modules()
            # Returns: ["module1", "module2", ...]
            ```
        """
        logger.info("Discovering modules...")
        
        modules = []
        
        if not self.modules_path.exists():
            logger.warning(f"Modules directory does not exist: {self.modules_path}")
            return modules
        
        for item in self.modules_path.iterdir():
            if not item.is_dir():
                continue
            
            if item.name.startswith("_"):
                continue
            
            # Check if module has module.py or __init__.py
            module_file = item / "module.py"
            if not module_file.exists():
                logger.debug(f"Skipping {item.name}: no module.py found")
                continue
            
            modules.append(item.name)
            logger.debug(f"Discovered module: {item.name}")
        
        logger.info(f"Discovered {len(modules)} modules: {modules}")
        return modules
    
    async def load_module(
        self,
        module_name: str,
        db_session: Any = None,
    ) -> BaseModule:
        """
        Load a module by name.
        
        Args:
            module_name: Name of the module to load
            db_session: Database session for settings (optional)
            
        Returns:
            Loaded BaseModule instance
            
        Raises:
            FileNotFoundError: If module not found
            ValueError: If module has invalid structure or dependencies
            ImportError: If module cannot be imported
            
        Example:
            ```python
            module = await loader.load_module("my_module")
            await module.on_load()
            ```
        """
        logger.info(f"Loading module: {module_name}")
        
        # Check if already loaded
        if module_name in self._loaded_modules:
            logger.warning(f"Module already loaded: {module_name}")
            return self._loaded_modules[module_name]
        
        module_path = self.modules_path / module_name
        
        if not module_path.exists():
            raise FileNotFoundError(f"Module directory not found: {module_path}")
        
        # Load manifest
        try:
            manifest = load_manifest(module_path)
            self._module_manifests[module_name] = manifest
            logger.debug(f"Manifest loaded: {manifest.name}")
        except Exception as e:
            logger.error(f"Failed to load manifest for {module_name}: {e}")
            raise ValueError(f"Invalid manifest: {e}") from e
        
        # Check dependencies
        await self._check_dependencies(manifest)
        
        # Load module code
        try:
            module = await self._import_module(module_name, module_path, db_session)
            
            # Call on_load
            await module.on_load()
            
            self._loaded_modules[module_name] = module
            module.enabled = manifest.enabled_by_default
            
            logger.info(f"Module loaded successfully: {module_name}")
            return module
            
        except Exception as e:
            logger.error(f"Failed to load module {module_name}: {e}", exc_info=True)
            raise
    
    async def unload_module(self, module_name: str) -> None:
        """
        Unload a module.
        
        Args:
            module_name: Name of the module to unload
            
        Example:
            ```python
            await loader.unload_module("my_module")
            ```
        """
        if module_name not in self._loaded_modules:
            logger.warning(f"Module not loaded: {module_name}")
            return
        
        logger.info(f"Unloading module: {module_name}")
        
        module = self._loaded_modules[module_name]
        
        try:
            # Call on_unload
            await module.on_unload()
            
            # Remove from loaded modules
            del self._loaded_modules[module_name]
            
            # Remove from sys.modules if present
            module_full_name = f"Modules.{module_name}"
            if module_full_name in sys.modules:
                del sys.modules[module_full_name]
            
            logger.info(f"Module unloaded successfully: {module_name}")
            
        except Exception as e:
            logger.error(f"Error unloading module {module_name}: {e}", exc_info=True)
    
    async def reload_module(
        self,
        module_name: str,
        db_session: Any = None,
    ) -> BaseModule:
        """
        Reload a module (unload and load again).
        
        Args:
            module_name: Name of the module to reload
            db_session: Database session for settings (optional)
            
        Returns:
            Reloaded BaseModule instance
            
        Example:
            ```python
            module = await loader.reload_module("my_module")
            ```
        """
        logger.info(f"Reloading module: {module_name}")
        
        if module_name in self._loaded_modules:
            await self.unload_module(module_name)
        
        return await self.load_module(module_name, db_session)
    
    async def _check_dependencies(self, manifest: ModuleManifest) -> None:
        """
        Check if module dependencies are satisfied.
        
        Args:
            manifest: Module manifest
            
        Raises:
            ValueError: If dependencies are not satisfied
        """
        if not manifest.dependencies:
            return
        
        missing = []
        
        for dep in manifest.dependencies:
            if dep not in self._loaded_modules:
                # Check if dependency module exists
                dep_path = self.modules_path / dep
                if not dep_path.exists():
                    missing.append(f"{dep} (not found)")
                else:
                    missing.append(f"{dep} (not loaded)")
        
        if missing:
            raise ValueError(
                f"Module {manifest.name} has unmet dependencies: {', '.join(missing)}"
            )
        
        logger.debug(f"All dependencies satisfied for {manifest.name}")
    
    async def _import_module(
        self,
        module_name: str,
        module_path: Path,
        db_session: Any = None,
    ) -> BaseModule:
        """
        Import and instantiate module.
        
        Args:
            module_name: Module name
            module_path: Path to module directory
            db_session: Database session
            
        Returns:
            BaseModule instance
            
        Raises:
            ImportError: If module cannot be imported
            ValueError: If module class not found or invalid
        """
        module_file = module_path / "module.py"
        
        if not module_file.exists():
            raise FileNotFoundError(f"module.py not found: {module_file}")
        
        # Create module spec
        spec = importlib.util.spec_from_file_location(
            f"Modules.{module_name}",
            module_file,
        )
        
        if not spec or not spec.loader:
            raise ImportError(f"Failed to create spec for {module_name}")
        
        # Load module
        module = importlib.util.module_from_spec(spec)
        sys.modules[f"Modules.{module_name}"] = module
        
        try:
            spec.loader.exec_module(module)
        except Exception as e:
            logger.error(f"Failed to execute module {module_name}: {e}")
            raise ImportError(f"Failed to import module {module_name}: {e}") from e
        
        # Find module class
        module_class = None
        for attr_name in dir(module):
            attr = getattr(module, attr_name, None)
            if (
                isinstance(attr, type)
                and issubclass(attr, BaseModule)
                and attr != BaseModule
            ):
                module_class = attr
                break
        
        if not module_class:
            raise ValueError(
                f"Module {module_name} does not define a BaseModule subclass"
            )
        
        # Get manifest
        manifest = self._module_manifests[module_name]
        
        # Get settings repository
        settings_repo = None
        if db_session:
            from Systems.core.database.repositories.settings_repository import (
                SettingsRepository,
            )
            
            settings_repo = SettingsRepository(db_session)
        
        # Instantiate module
        instance = module_class(manifest, settings_repo)
        
        logger.debug(f"Module class instantiated: {module_name}")
        return instance
    
    def get_loaded_module(self, module_name: str) -> BaseModule | None:
        """
        Get loaded module by name.
        
        Args:
            module_name: Module name
            
        Returns:
            BaseModule instance or None if not loaded
        """
        return self._loaded_modules.get(module_name)
    
    def get_loaded_modules(self) -> dict[str, BaseModule]:
        """
        Get all loaded modules.
        
        Returns:
            Dictionary of module_name -> BaseModule
        """
        return self._loaded_modules.copy()

