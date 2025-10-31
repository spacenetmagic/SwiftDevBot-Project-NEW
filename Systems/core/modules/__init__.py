"""
Module system package for SwiftDevBot.
"""

from Systems.core.modules.base_module import BaseModule
from Systems.core.modules.command_registry import CommandRegistry
from Systems.core.modules.loader import ModuleLoader
from Systems.core.modules.manager import ModuleManager
from Systems.core.modules.manifest import ModuleManifest, load_manifest
from Systems.core.modules.settings_manager import SettingsManager

__all__ = [
    "BaseModule",
    "ModuleManifest",
    "load_manifest",
    "ModuleLoader",
    "ModuleManager",
    "CommandRegistry",
    "SettingsManager",
]

