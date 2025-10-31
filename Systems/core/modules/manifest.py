"""
Module manifest system.
"""

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from Systems.core.logger import get_logger

logger = get_logger(__name__)


class ModuleManifest(BaseModel):
    """
    Module manifest schema.
    
    Defines module metadata, dependencies, commands, and settings.
    
    Example:
        ```python
        manifest = ModuleManifest(
            name="my_module",
            display_name="My Module",
            version="1.0.0",
            description="Example module",
            author="Author Name",
        )
        ```
    """
    
    # Basic info
    name: str = Field(..., description="Module name (identifier)")
    display_name: str = Field(..., description="Display name")
    version: str = Field(..., description="Module version")
    description: str = Field(default="", description="Module description")
    author: str = Field(default="", description="Module author")
    
    # Dependencies
    dependencies: list[str] = Field(
        default_factory=list,
        description="List of required module names",
    )
    
    # Commands
    commands: list[dict[str, Any]] = Field(
        default_factory=list,
        description="List of bot commands",
    )
    
    # Settings
    settings: dict[str, dict[str, Any]] = Field(
        default_factory=dict,
        description="Module settings schema",
    )
    
    # Languages
    languages: list[str] = Field(
        default_factory=lambda: ["en"],
        description="Supported languages",
    )
    
    # Background tasks
    background_tasks: list[str] = Field(
        default_factory=list,
        description="List of background task names",
    )
    
    # Flags
    enabled_by_default: bool = Field(
        default=False,
        description="Enable module by default",
    )
    
    # Metadata
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata",
    )
    
    model_config = {
        "extra": "allow",
    }


def load_manifest(module_path: Path) -> ModuleManifest:
    """
    Load module manifest from YAML file.
    
    Args:
        module_path: Path to module directory
        
    Returns:
        ModuleManifest instance
        
    Raises:
        FileNotFoundError: If manifest.yaml not found
        ValueError: If manifest is invalid
        
    Example:
        ```python
        manifest = load_manifest(Path("Modules/my_module"))
        print(manifest.name)
        ```
    """
    manifest_file = module_path / "manifest.yaml"
    
    if not manifest_file.exists():
        logger.warning(f"Manifest not found: {manifest_file}")
        # Return minimal manifest with name from directory
        return ModuleManifest(
            name=module_path.name,
            display_name=module_path.name.replace("_", " ").title(),
            version="1.0.0",
            description="",
        )
    
    try:
        with open(manifest_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        
        if not data:
            raise ValueError("Manifest file is empty")
        
        # Ensure name matches directory
        if "name" not in data:
            data["name"] = module_path.name
        
        manifest = ModuleManifest(**data)
        
        logger.debug(f"Manifest loaded: {manifest.name} v{manifest.version}")
        return manifest
        
    except yaml.YAMLError as e:
        logger.error(f"Failed to parse manifest YAML: {e}")
        raise ValueError(f"Invalid YAML in manifest: {e}") from e
    except Exception as e:
        logger.error(f"Failed to load manifest: {e}")
        raise ValueError(f"Invalid manifest: {e}") from e

