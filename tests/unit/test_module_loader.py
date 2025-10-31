"""
Unit tests for ModuleLoader.
"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from Systems.core.modules.loader import ModuleLoader
from Systems.core.modules.manifest import ModuleManifest


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
def sample_module_dir(modules_dir):
    """Create sample module directory."""
    module_dir = modules_dir / "test_module"
    module_dir.mkdir()
    
    # Create manifest.yaml
    manifest_file = module_dir / "manifest.yaml"
    manifest_file.write_text("""
name: test_module
display_name: Test Module
version: 1.0.0
description: Test module for testing
author: Test Author
""")
    
    # Create module.py
    module_file = module_dir / "module.py"
    module_file.write_text("""
from Systems.core.modules.base_module import BaseModule
from Systems.core.modules.manifest import ModuleManifest

class TestModule(BaseModule):
    async def on_load(self):
        pass
    
    async def on_unload(self):
        pass
""")
    
    return module_dir


@pytest.mark.asyncio
async def test_discover_modules_empty(loader: ModuleLoader) -> None:
    """Test discovering modules in empty directory."""
    modules = await loader.discover_modules()
    
    assert modules == []


@pytest.mark.asyncio
async def test_discover_modules(loader: ModuleLoader, sample_module_dir) -> None:
    """Test discovering modules."""
    modules = await loader.discover_modules()
    
    assert "test_module" in modules


@pytest.mark.asyncio
async def test_discover_modules_no_module_py(loader: ModuleLoader, modules_dir) -> None:
    """Test that modules without module.py are not discovered."""
    module_dir = modules_dir / "incomplete_module"
    module_dir.mkdir()
    
    # No module.py file
    modules = await loader.discover_modules()
    
    assert "incomplete_module" not in modules


@pytest.mark.asyncio
async def test_load_module(loader: ModuleLoader, sample_module_dir) -> None:
    """Test loading a module."""
    module = await loader.load_module("test_module")
    
    assert module is not None
    assert module.name == "test_module"
    assert module.version == "1.0.0"


@pytest.mark.asyncio
async def test_load_module_not_found(loader: ModuleLoader) -> None:
    """Test loading non-existent module."""
    with pytest.raises(FileNotFoundError):
        await loader.load_module("nonexistent_module")


@pytest.mark.asyncio
async def test_unload_module(loader: ModuleLoader, sample_module_dir) -> None:
    """Test unloading a module."""
    module = await loader.load_module("test_module")
    
    await loader.unload_module("test_module")
    
    assert loader.get_loaded_module("test_module") is None


@pytest.mark.asyncio
async def test_unload_module_not_loaded(loader: ModuleLoader) -> None:
    """Test unloading a module that's not loaded."""
    # Should not raise error
    await loader.unload_module("nonexistent_module")


@pytest.mark.asyncio
async def test_reload_module(loader: ModuleLoader, sample_module_dir) -> None:
    """Test reloading a module."""
    module1 = await loader.load_module("test_module")
    
    module2 = await loader.reload_module("test_module")
    
    assert module2 is not None
    assert module2.name == module1.name


@pytest.mark.asyncio
async def test_get_loaded_module(loader: ModuleLoader, sample_module_dir) -> None:
    """Test getting loaded module."""
    module = await loader.load_module("test_module")
    
    loaded = loader.get_loaded_module("test_module")
    
    assert loaded == module


@pytest.mark.asyncio
async def test_get_loaded_module_not_loaded(loader: ModuleLoader) -> None:
    """Test getting module that's not loaded."""
    module = loader.get_loaded_module("nonexistent")
    
    assert module is None


@pytest.mark.asyncio
async def test_get_loaded_modules(loader: ModuleLoader, sample_module_dir) -> None:
    """Test getting all loaded modules."""
    await loader.load_module("test_module")
    
    modules = loader.get_loaded_modules()
    
    assert "test_module" in modules
    assert len(modules) == 1

