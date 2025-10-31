"""
Unit tests for ModuleManager.
"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from Systems.core.modules.loader import ModuleLoader
from Systems.core.modules.manager import ModuleManager


@pytest.fixture
def modules_dir(tmp_path):
    """Create temporary modules directory."""
    modules_path = tmp_path / "Modules"
    modules_path.mkdir()
    return modules_path


@pytest.fixture
def loader(modules_dir):
    """Create ModuleLoader instance."""
    return ModuleLoader(modules_dir)


@pytest.fixture
def mock_dispatcher():
    """Create mock dispatcher."""
    dispatcher = MagicMock()
    dispatcher.include_router = MagicMock()
    return dispatcher


@pytest.fixture
def mock_db_session():
    """Create mock database session."""
    session = AsyncMock()
    session.commit = AsyncMock()
    return session


@pytest.fixture
async def manager(loader, mock_dispatcher, mock_db_session):
    """Create ModuleManager instance."""
    manager = ModuleManager(loader, mock_dispatcher, mock_db_session)
    yield manager
    # Cleanup if needed


@pytest.mark.asyncio
async def test_manager_initialization(manager: ModuleManager) -> None:
    """Test module manager initialization."""
    assert manager.loader is not None
    assert manager.dispatcher is not None


@pytest.mark.asyncio
async def test_load_all_modules(manager: ModuleManager, modules_dir) -> None:
    """Test loading all modules."""
    # Create a test module
    module_dir = modules_dir / "test_module"
    module_dir.mkdir()
    
    manifest_file = module_dir / "manifest.yaml"
    manifest_file.write_text("""
name: test_module
display_name: Test Module
version: 1.0.0
""")
    
    module_file = module_dir / "module.py"
    module_file.write_text("""
from Systems.core.modules.base_module import BaseModule

class TestModule(BaseModule):
    async def on_load(self):
        pass
    
    async def on_unload(self):
        pass
""")
    
    modules = await manager.load_all_modules()
    
    assert len(modules) >= 1
    assert "test_module" in modules


@pytest.mark.asyncio
async def test_enable_module(manager: ModuleManager, modules_dir) -> None:
    """Test enabling a module."""
    # Create test module
    module_dir = modules_dir / "test_module"
    module_dir.mkdir()
    
    manifest_file = module_dir / "manifest.yaml"
    manifest_file.write_text("""
name: test_module
display_name: Test Module
version: 1.0.0
""")
    
    module_file = module_dir / "module.py"
    module_file.write_text("""
from Systems.core.modules.base_module import BaseModule

class TestModule(BaseModule):
    async def on_load(self):
        pass
    
    async def on_unload(self):
        pass
""")
    
    module = await manager.enable_module("test_module")
    
    assert module is not None
    assert module.enabled is True


@pytest.mark.asyncio
async def test_disable_module(manager: ModuleManager, modules_dir) -> None:
    """Test disabling a module."""
    # Create and load module first
    module_dir = modules_dir / "test_module"
    module_dir.mkdir()
    
    manifest_file = module_dir / "manifest.yaml"
    manifest_file.write_text("""
name: test_module
display_name: Test Module
version: 1.0.0
""")
    
    module_file = module_dir / "module.py"
    module_file.write_text("""
from Systems.core.modules.base_module import BaseModule

class TestModule(BaseModule):
    async def on_load(self):
        pass
    
    async def on_unload(self):
        pass
""")
    
    await manager.enable_module("test_module")
    await manager.disable_module("test_module")
    
    module = manager.loader.get_loaded_module("test_module")
    assert module is not None
    assert module.enabled is False


@pytest.mark.asyncio
async def test_reload_module(manager: ModuleManager, modules_dir) -> None:
    """Test reloading a module."""
    # Create test module
    module_dir = modules_dir / "test_module"
    module_dir.mkdir()
    
    manifest_file = module_dir / "manifest.yaml"
    manifest_file.write_text("""
name: test_module
display_name: Test Module
version: 1.0.0
""")
    
    module_file = module_dir / "module.py"
    module_file.write_text("""
from Systems.core.modules.base_module import BaseModule

class TestModule(BaseModule):
    async def on_load(self):
        pass
    
    async def on_unload(self):
        pass
""")
    
    module1 = await manager.enable_module("test_module")
    
    module2 = await manager.reload_module("test_module")
    
    assert module2 is not None
    assert module2.name == module1.name


@pytest.mark.asyncio
async def test_get_available_modules(manager: ModuleManager, modules_dir) -> None:
    """Test getting available modules."""
    # Create test module
    module_dir = modules_dir / "test_module"
    module_dir.mkdir()
    
    manifest_file = module_dir / "manifest.yaml"
    manifest_file.write_text("""
name: test_module
display_name: Test Module
version: 1.0.0
""")
    
    module_file = module_dir / "module.py"
    module_file.write_text("""
from Systems.core.modules.base_module import BaseModule

class TestModule(BaseModule):
    async def on_load(self):
        pass
    
    async def on_unload(self):
        pass
""")
    
    await manager.load_all_modules()
    
    modules = await manager.get_available_modules()
    
    assert len(modules) >= 1

