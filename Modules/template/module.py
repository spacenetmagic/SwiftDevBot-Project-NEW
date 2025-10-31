"""
Example Module Template for SwiftDevBot

This module demonstrates the basic structure of a SwiftDevBot module.
Copy this template and modify it to create your own module.

Usage:
    1. Copy Modules/template/ to Modules/your_module/
    2. Update manifest.yaml with your module information
    3. Modify module.py with your functionality
    4. Add handlers/commands.py with command handlers
    5. Update __init__.py
"""

from Systems.core.modules.base_module import BaseModule
from Systems.core.modules.manifest import ModuleManifest
from Systems.core.events import event_bus
from Systems.core.logger import get_logger

logger = get_logger(__name__)


class ExampleModule(BaseModule):
    """
    Example module demonstrating SwiftDevBot module structure.
    
    This module shows:
    - Basic module structure
    - Event handling
    - Command registration
    - Settings usage
    - Background tasks
    """
    
    def __init__(
        self,
        manifest: ModuleManifest,
        settings_repo=None,
    ) -> None:
        """Initialize the module."""
        super().__init__(manifest, settings_repo)
        
        # Initialize module-specific variables
        self._task_definitions = {
            "cleanup_old_data": {
                "type": "interval",
                "config": {"seconds": 3600},  # Run every hour
            },
            "send_daily_report": {
                "type": "cron",
                "config": {"hour": 9, "minute": 0},  # Run daily at 9:00 AM
            },
        }
        
        logger.info(f"ExampleModule initialized: {self.name}")
    
    async def on_load(self) -> None:
        """
        Called when module is loaded.
        
        Use this to:
        - Register event handlers
        - Initialize resources
        - Set up database connections
        """
        logger.info(f"Loading module: {self.name}")
        
        # Subscribe to events
        await event_bus.subscribe("user.created", self._on_user_created)
        await event_bus.subscribe("user.updated", self._on_user_updated)
        
        # Register command handlers (if not using router directly)
        # Commands are automatically registered from manifest
        
        logger.info(f"Module {self.name} loaded successfully")
    
    async def on_unload(self) -> None:
        """
        Called when module is unloaded.
        
        Use this to:
        - Clean up resources
        - Unsubscribe from events
        - Close database connections
        """
        logger.info(f"Unloading module: {self.name}")
        
        # Unsubscribe from events
        await event_bus.unsubscribe("user.created", self._on_user_created)
        await event_bus.unsubscribe("user.updated", self._on_user_updated)
        
        logger.info(f"Module {self.name} unloaded successfully")
    
    async def on_enable(self) -> None:
        """
        Called when module is enabled.
        
        Override if you need special handling when module is enabled.
        """
        logger.info(f"Module {self.name} enabled")
        
        # Example: Get a setting value
        max_requests = await self.get_setting("max_requests", default=100)
        logger.debug(f"Max requests setting: {max_requests}")
    
    async def on_disable(self) -> None:
        """
        Called when module is disabled.
        
        Override if you need special handling when module is disabled.
        """
        logger.info(f"Module {self.name} disabled")
    
    # Event Handlers
    
    async def _on_user_created(self, data: dict) -> None:
        """
        Handle user.created event.
        
        Args:
            data: Event data containing user information
        """
        logger.info(f"User created event received: {data}")
        
        # Example: Send welcome message
        user_id = data.get("user_id")
        if user_id:
            logger.debug(f"Processing welcome for user: {user_id}")
    
    async def _on_user_updated(self, data: dict) -> None:
        """
        Handle user.updated event.
        
        Args:
            data: Event data containing user information
        """
        logger.info(f"User updated event received: {data}")
    
    # Background Tasks
    # These functions will be scheduled automatically based on manifest.yaml
    
    async def cleanup_old_data(self) -> None:
        """
        Background task: Clean up old data.
        
        This task runs every hour (as defined in manifest.yaml).
        """
        logger.info("Running cleanup_old_data background task")
        
        # Example: Clean up old records
        # Your cleanup logic here
        
        logger.debug("Cleanup completed")
    
    async def send_daily_report(self) -> None:
        """
        Background task: Send daily report.
        
        This task runs daily at 9:00 AM (as defined in manifest.yaml).
        """
        logger.info("Running send_daily_report background task")
        
        # Example: Generate and send report
        # Your report logic here
        
        logger.debug("Daily report sent")
    
    # Command Handlers
    # These are registered in handlers/commands.py and called by the router
    
    async def handle_example_command(self, message) -> None:
        """
        Handle /example command.
        
        This is called when user sends /example command.
        """
        logger.info(f"Example command received from user: {message.from_user.id}")
        
        # Get user-specific setting
        theme = await self.get_setting("theme", user_id=message.from_user.id, default="light")
        
        # Respond to user
        await message.answer(f"Example command! Your theme is: {theme}")
    
    async def handle_example_admin_command(self, message) -> None:
        """
        Handle /example_admin command (admin-only).
        
        This is called when admin sends /example_admin command.
        """
        logger.info(f"Example admin command received from user: {message.from_user.id}")
        
        # Get admin setting
        max_requests = await self.get_setting("max_requests", default=100)
        
        # Respond to admin
        await message.answer(f"Admin command! Max requests: {max_requests}")

