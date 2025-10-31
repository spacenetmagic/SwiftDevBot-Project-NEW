"""
CLI commands for module management.
"""

import asyncio
import shutil
from pathlib import Path
from typing import Optional

import click
from click import Group

from Systems.core.database import get_session_factory
from Systems.core.logger import get_logger
from Systems.core.modules.loader import ModuleLoader
from Systems.core.modules.manager import ModuleManager
from Systems.core.utils.config import Config

logger = get_logger(__name__)


@click.group(name="module")
def module_group() -> None:
    """Module management commands."""
    pass


@module_group.command("install")
@click.argument("path", type=click.Path(exists=True))
@click.option("--name", help="Module name (defaults to directory name)")
def install(path: str, name: Optional[str]) -> None:
    """
    Install a module from a directory.
    
    Args:
        path: Path to module directory
        name: Module name (optional)
    
    Example:
        sdb module install ./my_module
        sdb module install /path/to/module --name custom_name
    """
    try:
        module_path = Path(path).resolve()
        
        if not module_path.is_dir():
            logger.error(f"Path is not a directory: {path}")
            click.echo(f"Error: {path} is not a directory", err=True)
            click.get_current_context().exit(1)
        
        # Check for manifest.yaml
        manifest_file = module_path / "manifest.yaml"
        if not manifest_file.exists():
            logger.error(f"manifest.yaml not found in: {path}")
            click.echo(f"Error: manifest.yaml not found in {path}", err=True)
            click.get_current_context().exit(1)
        
        # Check for module.py
        module_file = module_path / "module.py"
        if not module_file.exists():
            logger.error(f"module.py not found in: {path}")
            click.echo(f"Error: module.py not found in {path}", err=True)
            click.get_current_context().exit(1)
        
        # Determine module name
        module_name = name or module_path.name
        
        # Get modules directory
        config = Config()
        modules_dir = Path("Modules")
        modules_dir.mkdir(exist_ok=True)
        
        target_dir = modules_dir / module_name
        
        if target_dir.exists():
            logger.error(f"Module already exists: {module_name}")
            click.echo(f"Error: Module {module_name} already exists", err=True)
            click.get_current_context().exit(1)
        
        # Copy module
        logger.info(f"Installing module {module_name} from {module_path}")
        shutil.copytree(module_path, target_dir)
        
        click.echo(f"✓ Module {module_name} installed successfully")
        logger.info(f"Module {module_name} installed to {target_dir}")
        
    except Exception as e:
        logger.error(f"Failed to install module: {e}", exc_info=True)
        click.echo(f"Error: {str(e)}", err=True)
        click.get_current_context().exit(1)


@module_group.command("uninstall")
@click.argument("name")
@click.option("--force", is_flag=True, help="Force removal without confirmation")
def uninstall(name: str, force: bool) -> None:
    """
    Uninstall a module.
    
    Args:
        name: Module name
        force: Force removal without confirmation
    
    Example:
        sdb module uninstall example_module
        sdb module uninstall example_module --force
    """
    try:
        modules_dir = Path("Modules")
        module_dir = modules_dir / name
        
        if not module_dir.exists():
            logger.error(f"Module not found: {name}")
            click.echo(f"Error: Module {name} not found", err=True)
            click.get_current_context().exit(1)
        
        if not force:
            if not click.confirm(f"Are you sure you want to uninstall module {name}?"):
                click.echo("Cancelled")
                return
        
        logger.info(f"Uninstalling module {name}")
        shutil.rmtree(module_dir)
        
        click.echo(f"✓ Module {name} uninstalled successfully")
        logger.info(f"Module {name} uninstalled")
        
    except Exception as e:
        logger.error(f"Failed to uninstall module: {e}", exc_info=True)
        click.echo(f"Error: {str(e)}", err=True)
        click.get_current_context().exit(1)


@module_group.command("list")
@click.option("--enabled", is_flag=True, help="Show only enabled modules")
@click.option("--disabled", is_flag=True, help="Show only disabled modules")
def list_modules(enabled: bool, disabled: bool) -> None:
    """
    List all installed modules.
    
    Args:
        enabled: Show only enabled modules
        disabled: Show only disabled modules
    
    Example:
        sdb module list
        sdb module list --enabled
        sdb module list --disabled
    """
    try:
        modules_dir = Path("Modules")
        
        if not modules_dir.exists():
            click.echo("No modules directory found")
            return
        
        modules = [d.name for d in modules_dir.iterdir() if d.is_dir() and not d.name.startswith("_")]
        
        if not modules:
            click.echo("No modules installed")
            return
        
        # Get loaded modules if manager is available
        try:
            loader = ModuleLoader(modules_dir)
            loaded = loader.get_loaded_modules()
            
            click.echo(f"Installed modules ({len(modules)}):")
            click.echo("")
            
            for module_name in sorted(modules):
                module = loaded.get(module_name)
                status = "✓ Enabled" if module and module.enabled else "✗ Disabled"
                
                if enabled and (not module or not module.enabled):
                    continue
                if disabled and (module and module.enabled):
                    continue
                
                version = module.manifest.version if module else "?"
                click.echo(f"  {status}  {module_name} (v{version})")
                
        except Exception:
            # Fallback if manager not available
            click.echo(f"Installed modules ({len(modules)}):")
            for module_name in sorted(modules):
                click.echo(f"  - {module_name}")
        
    except Exception as e:
        logger.error(f"Failed to list modules: {e}", exc_info=True)
        click.echo(f"Error: {str(e)}", err=True)
        click.get_current_context().exit(1)


async def _module_action(name: str, action: str) -> None:
    """Helper function for module actions."""
    modules_dir = Path("Modules")
    loader = ModuleLoader(modules_dir)
    
    async with get_session_factory()() as session:
        manager = ModuleManager(loader, db_session=session)
        
        if action == "enable":
            await manager.enable_module(name)
            click.echo(f"✓ Module {name} enabled")
        elif action == "disable":
            await manager.disable_module(name)
            click.echo(f"✓ Module {name} disabled")
        elif action == "reload":
            await manager.reload_module(name)
            click.echo(f"✓ Module {name} reloaded")


@module_group.command("enable")
@click.argument("name")
def enable(name: str) -> None:
    """
    Enable a module.
    
    Args:
        name: Module name
    
    Example:
        sdb module enable example_module
    """
    try:
        asyncio.run(_module_action(name, "enable"))
    except Exception as e:
        logger.error(f"Failed to enable module: {e}", exc_info=True)
        click.echo(f"Error: {str(e)}", err=True)
        click.get_current_context().exit(1)


@module_group.command("disable")
@click.argument("name")
def disable(name: str) -> None:
    """
    Disable a module.
    
    Args:
        name: Module name
    
    Example:
        sdb module disable example_module
    """
    try:
        asyncio.run(_module_action(name, "disable"))
    except Exception as e:
        logger.error(f"Failed to disable module: {e}", exc_info=True)
        click.echo(f"Error: {str(e)}", err=True)
        click.get_current_context().exit(1)


@module_group.command("reload")
@click.argument("name")
def reload(name: str) -> None:
    """
    Reload a module (hot reload).
    
    Args:
        name: Module name
    
    Example:
        sdb module reload example_module
    """
    try:
        asyncio.run(_module_action(name, "reload"))
    except Exception as e:
        logger.error(f"Failed to reload module: {e}", exc_info=True)
        click.echo(f"Error: {str(e)}", err=True)
        click.get_current_context().exit(1)


@module_group.command("watch")
def watch() -> None:
    """
    Watch for module changes and auto-reload (development mode).
    
    Example:
        sdb module watch
    """
    try:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
        
        modules_dir = Path("Modules")
        
        if not modules_dir.exists():
            click.echo("No modules directory found")
            click.get_current_context().exit(1)
        
        class ModuleHandler(FileSystemEventHandler):
            """Handler for module file changes."""
            
            def on_modified(self, event):
                if not event.is_directory and event.src_path.endswith(".py"):
                    module_name = Path(event.src_path).parent.name
                    if module_name != "__pycache__":
                        logger.info(f"Module file changed: {module_name}")
                        try:
                            asyncio.run(_module_action(module_name, "reload"))
                            click.echo(f"✓ Auto-reloaded module: {module_name}")
                        except Exception as e:
                            click.echo(f"✗ Failed to reload {module_name}: {e}", err=True)
        
        handler = ModuleHandler()
        observer = Observer()
        observer.schedule(handler, str(modules_dir), recursive=True)
        observer.start()
        
        click.echo(f"Watching modules directory: {modules_dir}")
        click.echo("Press Ctrl+C to stop")
        
        try:
            while True:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
            click.echo("\nStopped watching")
        
        observer.join()
        
    except ImportError:
        click.echo("Error: watchdog not installed. Install it with: pip install watchdog", err=True)
        click.get_current_context().exit(1)
    except Exception as e:
        logger.error(f"Failed to watch modules: {e}", exc_info=True)
        click.echo(f"Error: {str(e)}", err=True)
        click.get_current_context().exit(1)


@module_group.command("update")
@click.argument("name")
def update(name: str) -> None:
    """
    Update a module (reload and apply changes).
    
    Args:
        name: Module name
    
    Example:
        sdb module update example_module
    """
    try:
        # For now, update is same as reload
        # In future, this could fetch updates from remote source
        asyncio.run(_module_action(name, "reload"))
        click.echo(f"✓ Module {name} updated")
    except Exception as e:
        logger.error(f"Failed to update module: {e}", exc_info=True)
        click.echo(f"Error: {str(e)}", err=True)
        click.get_current_context().exit(1)

