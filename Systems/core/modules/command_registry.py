"""
Command registry for module commands.
"""

from typing import Any

from aiogram.utils.keyboard import InlineKeyboardBuilder

from Systems.core.database.models.user import User
from Systems.core.logger import get_logger
from Systems.core.modules.base_module import BaseModule
from Systems.core.modules.manager import ModuleManager

logger = get_logger(__name__)


class CommandInfo:
    """Command information."""
    
    def __init__(
        self,
        name: str,
        description: str,
        admin_only: bool = False,
        module: str = "",
    ) -> None:
        """Initialize command info."""
        self.name = name
        self.description = description
        self.admin_only = admin_only
        self.module = module


class CommandRegistry:
    """
    Command registry for module commands.
    
    Manages command registration and provides filtered command lists for users.
    
    Example:
        ```python
        registry = CommandRegistry(manager)
        commands = registry.get_commands_for_user(user)
        keyboard = registry.build_module_keyboard(user)
        ```
    """
    
    def __init__(self, manager: ModuleManager) -> None:
        """
        Initialize command registry.
        
        Args:
            manager: Module manager instance
        """
        self.manager = manager
        self._commands: dict[str, CommandInfo] = {}
        
        logger.info("CommandRegistry initialized")
    
    def register_module_commands(self, module: BaseModule) -> None:
        """
        Register commands from a module.
        
        Args:
            module: Module instance
        """
        manifest = module.manifest
        
        if not manifest.commands:
            logger.debug(f"No commands in module: {module.name}")
            return
        
        for cmd_data in manifest.commands:
            cmd_name = cmd_data.get("name", "")
            cmd_desc = cmd_data.get("description", "")
            admin_only = cmd_data.get("admin", False)
            
            if not cmd_name:
                logger.warning(f"Command without name in module {module.name}")
                continue
            
            command = CommandInfo(
                name=cmd_name,
                description=cmd_desc,
                admin_only=admin_only,
                module=module.name,
            )
            
            self._commands[f"{module.name}.{cmd_name}"] = command
            logger.debug(f"Command registered: {module.name}.{cmd_name}")
    
    def get_commands_for_user(self, user: User) -> list[CommandInfo]:
        """
        Get available commands for a user.
        
        Filters commands based on user role and admin_only flag.
        
        Args:
            user: User object
            
        Returns:
            List of available commands
            
        Example:
            ```python
            commands = registry.get_commands_for_user(user)
            for cmd in commands:
                print(cmd.name, cmd.description)
            ```
        """
        from Systems.core.database.models.user import UserRole
        
        available = []
        
        for command in self._commands.values():
            # Filter admin-only commands
            if command.admin_only:
                if user.role not in {UserRole.ADMIN, UserRole.SUPER_ADMIN}:
                    continue
            
            available.append(command)
        
        logger.debug(f"Found {len(available)} commands for user {user.telegram_id}")
        return available
    
    def get_commands_by_category(
        self,
        user: User,
    ) -> dict[str, list[CommandInfo]]:
        """
        Get commands grouped by module/category.
        
        Args:
            user: User object
            
        Returns:
            Dictionary of module_name -> list of commands
            
        Example:
            ```python
            categories = registry.get_commands_by_category(user)
            for module, commands in categories.items():
                print(f"{module}: {len(commands)} commands")
            ```
        """
        commands = self.get_commands_for_user(user)
        
        categories: dict[str, list[CommandInfo]] = {}
        
        for command in commands:
            module_name = command.module
            if module_name not in categories:
                categories[module_name] = []
            categories[module_name].append(command)
        
        return categories
    
    def build_module_keyboard(
        self,
        user: User,
    ) -> InlineKeyboardBuilder:
        """
        Build inline keyboard with available module commands.
        
        Args:
            user: User object
            
        Returns:
            InlineKeyboardBuilder instance
            
        Example:
            ```python
            keyboard = registry.build_module_keyboard(user)
            await message.answer("Choose module:", reply_markup=keyboard.as_markup())
            ```
        """
        keyboard = InlineKeyboardBuilder()
        
        categories = self.get_commands_by_category(user)
        
        for module_name, commands in categories.items():
            # Add module header
            keyboard.button(
                text=f"📦 {module_name}",
                callback_data=f"module:{module_name}:info",
            )
            
            # Add commands (limit to 3 per module to avoid huge keyboard)
            for cmd in commands[:3]:
                keyboard.button(
                    text=f"  • {cmd.name}",
                    callback_data=f"cmd:{module_name}:{cmd.name}",
                )
            
            keyboard.adjust(1)  # One button per row
        
        return keyboard

