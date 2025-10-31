# Module Development Guide

This guide explains how to create, develop, and deploy modules for SwiftDevBot.

## Overview

Modules are hot-reloadable extensions that add functionality to SwiftDevBot. They can:
- Register bot commands
- Define settings (user/admin level)
- Subscribe to events
- Schedule background tasks
- Access database and services

## Module Structure

Every module must have this structure:

```
Modules/
└── my_module/
    ├── __init__.py              # Module package init
    ├── module.py                # Main module class
    ├── manifest.yaml            # Module metadata
    ├── handlers/                # Command handlers
    │   ├── __init__.py
    │   └── commands.py
    └── (optional files)
        ├── models.py            # Database models (if needed)
        ├── services.py           # Business logic
        └── utils.py             # Helper functions
```

## Quick Start

1. **Copy the template:**
   ```bash
   cp -r Modules/template Modules/my_module
   ```

2. **Edit manifest.yaml:**
   ```yaml
   name: my_module
   display_name: My Module
   version: 1.0.0
   description: My awesome module
   author: Your Name
   ```

3. **Implement your module:**
   ```python
   # module.py
   from Systems.core.modules.base_module import BaseModule
   
   class MyModule(BaseModule):
       async def on_load(self) -> None:
           # Called when module loads
           pass
       
       async def on_unload(self) -> None:
           # Called when module unloads
           pass
   ```

4. **Enable your module:**
   ```bash
   sdb module enable my_module
   ```

## Manifest (manifest.yaml)

The manifest defines module metadata and configuration.

### Basic Fields

```yaml
# Required
name: my_module              # Module name (must match directory)
display_name: My Module      # Display name for UI
version: 1.0.0               # Semantic versioning
description: Module description
author: Your Name

# Optional
enabled_by_default: false   # Auto-enable on load
dependencies: []            # Other module names
languages: ["en", "ru"]     # Supported languages
```

### Commands

Define bot commands your module provides:

```yaml
commands:
  - name: start              # Command name (/start)
    description: Start command
    admin: false             # Admin-only if true
  
  - name: admin_cmd          # /admin_cmd
    description: Admin command
    admin: true
```

### Settings

Define module settings:

```yaml
settings:
  # User-level setting (per-user)
  theme:
    type: string
    default: "light"
    description: "User theme preference"
    enum: ["light", "dark"]  # Optional: allowed values
  
  # Admin-level setting (global)
  max_requests:
    type: integer
    default: 100
    min: 1                   # Optional: minimum value
    max: 1000                # Optional: maximum value
    description: "Max requests per user"
```

**Setting Types:**
- `string` - Text value
- `integer` - Whole number
- `float` - Decimal number
- `boolean` - True/false
- `array` - List of values
- `object` - JSON object

### Background Tasks

Define background tasks:

```yaml
background_tasks:
  - cleanup_old_data        # Function name in module.py
  - send_daily_report
```

Tasks are automatically scheduled based on type:
- **Interval**: `cleanup_old_data` runs every hour
- **Cron**: `send_daily_report` runs daily at 9 AM

See [Background Tasks](#background-tasks) section.

### Complete Example

```yaml
name: example_module
display_name: Example Module
version: 1.0.0
description: An example module
author: Your Name

dependencies: []

commands:
  - name: example
    description: Example command
    admin: false
  - name: example_admin
    description: Admin command
    admin: true

settings:
  theme:
    type: string
    default: "light"
    description: "Theme preference"
  max_items:
    type: integer
    default: 10
    min: 1
    max: 100
    description: "Maximum items"

background_tasks:
  - cleanup_task
  - report_task

enabled_by_default: false

metadata:
  homepage: https://github.com/yourusername/module
  license: MIT
```

## Module Class

Your module must inherit from `BaseModule`:

```python
from Systems.core.modules.base_module import BaseModule
from Systems.core.modules.manifest import ModuleManifest

class MyModule(BaseModule):
    def __init__(self, manifest: ModuleManifest, settings_repo=None):
        super().__init__(manifest, settings_repo)
        # Initialize your module
    
    async def on_load(self) -> None:
        """Called when module is loaded."""
        # Register event handlers
        # Initialize resources
        pass
    
    async def on_unload(self) -> None:
        """Called when module is unloaded."""
        # Clean up resources
        # Unsubscribe from events
        pass
    
    async def on_enable(self) -> None:
        """Called when module is enabled."""
        # Start services
        # Register handlers
        pass
    
    async def on_disable(self) -> None:
        """Called when module is disabled."""
        # Stop services
        # Unregister handlers
        pass
```

### Lifecycle Methods

| Method | When Called | Purpose |
|--------|-------------|---------|
| `__init__` | Module instantiation | Initialize variables |
| `on_load` | Module loaded | Setup resources, subscribe to events |
| `on_enable` | Module enabled | Register handlers, start tasks |
| `on_disable` | Module disabled | Unregister handlers, stop tasks |
| `on_unload` | Module unloaded | Cleanup, unsubscribe from events |

## Command Handlers

Create command handlers in `handlers/commands.py`:

```python
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from Systems.core.rbac.middleware import require_role
from Systems.core.database.models.user import UserRole

router = Router(name="my_module_commands")

@router.message(Command("start"))
async def handle_start(message: Message) -> None:
    """Handle /start command."""
    await message.answer("Hello from my module!")

@router.message(Command("admin"))
@require_role(UserRole.ADMIN)
async def handle_admin(message: Message) -> None:
    """Admin-only command."""
    await message.answer("Admin command executed!")
```

Then register the router in `on_enable()`:

```python
async def on_enable(self) -> None:
    from .handlers.commands import router
    # Router should be registered via module manager
    pass
```

## Settings Management

Access settings using `get_setting()`:

```python
# Get user setting
theme = await self.get_setting(
    "theme",
    user_id=user.telegram_id,
    default="light"
)

# Get admin setting
max_users = await self.get_setting(
    "max_users",
    default=100
)

# Set user setting
await self.set_user_setting(
    "theme",
    "dark",
    user_id=user.telegram_id,
    manifest=self.manifest
)

# Set admin setting
await self.set_admin_setting(
    "max_users",
    500,
    manifest=self.manifest
)
```

## Event Bus Integration

Subscribe to events:

```python
from Systems.core.events import event_bus

async def on_load(self) -> None:
    # Subscribe to events
    await event_bus.subscribe("user.created", self._on_user_created)
    await event_bus.subscribe("user.updated", self._on_user_updated)

async def _on_user_created(self, data: dict) -> None:
    """Handle user.created event."""
    user_id = data.get("user_id")
    # Process event
    pass

async def on_unload(self) -> None:
    # Unsubscribe
    await event_bus.unsubscribe("user.created", self._on_user_created)
```

Emit events:

```python
await event_bus.emit("my_module.custom_event", {
    "data": "value",
    "timestamp": datetime.now().isoformat()
})
```

### Common Events

| Event | Data | When |
|-------|------|------|
| `user.created` | `{user_id, username}` | New user registered |
| `user.updated` | `{user_id, changes}` | User profile updated |
| `module.loaded` | `{module_name}` | Module loaded |
| `module.enabled` | `{module_name}` | Module enabled |
| `command.executed` | `{user_id, command}` | Command executed |

## Background Tasks

Define background tasks in manifest:

```yaml
background_tasks:
  - cleanup_old_data      # Interval: every hour
  - send_daily_report     # Cron: daily at 9 AM
```

Implement in `module.py`:

```python
async def cleanup_old_data(self) -> None:
    """Runs every hour."""
    # Cleanup logic
    logger.info("Cleaning up old data")

async def send_daily_report(self) -> None:
    """Runs daily at 9 AM."""
    # Send report logic
    logger.info("Sending daily report")
```

Tasks are automatically registered based on function name.

## Database Access

Access database through repositories:

```python
from Systems.core.database import get_session_factory
from Systems.core.database.repositories.user_repository import UserRepository

async def get_user_count(self) -> int:
    async with get_session_factory()() as session:
        user_repo = UserRepository(session)
        users = await user_repo.get_all()
        return len(users)
```

## Error Handling

Always handle errors gracefully:

```python
async def on_load(self) -> None:
    try:
        # Your code
        pass
    except Exception as e:
        logger.error(f"Error loading module: {e}", exc_info=True)
        raise  # Re-raise to indicate load failure
```

## Testing Modules

Create tests in `tests/modules/test_my_module.py`:

```python
import pytest
from Systems.core.modules.loader import ModuleLoader

@pytest.mark.asyncio
async def test_module_loads():
    loader = ModuleLoader(Path("Modules"))
    module = await loader.load_module("my_module")
    assert module is not None

@pytest.mark.asyncio
async def test_module_command():
    # Test command handler
    pass
```

## Best Practices

1. **Keep modules focused**: One module, one purpose
2. **Handle errors**: Always wrap risky operations in try/except
3. **Log appropriately**: Use logger, not print
4. **Document code**: Add docstrings to all functions
5. **Version your module**: Use semantic versioning
6. **Test your module**: Write tests before deployment
7. **Clean up resources**: Always clean up in `on_unload()`
8. **Respect RBAC**: Check permissions before sensitive operations

## Module Template

Use the provided template:

```bash
sdb module install ./Modules/template
# Copy and modify to create your module
```

The template includes:
- Complete module structure
- Example manifest.yaml
- Command handler examples
- Settings examples
- Event handlers
- Background tasks

## Publishing Modules

1. **Version your module** in manifest.yaml
2. **Write documentation** (README.md in module directory)
3. **Add tests**
4. **Create GitHub release** or publish to package registry
5. **Update module registry** (if applicable)

## Common Patterns

### Pattern: Command with Settings

```python
@router.message(Command("configure"))
async def handle_configure(message: Message) -> None:
    # Get current setting
    current = await module.get_setting(
        "theme",
        user_id=message.from_user.id,
        default="light"
    )
    await message.answer(f"Current theme: {current}")
```

### Pattern: Admin Command

```python
@router.message(Command("admin_config"))
@require_role(UserRole.ADMIN)
async def handle_admin_config(message: Message) -> None:
    # Admin-only setting
    max_users = await module.get_setting("max_users", default=100)
    await message.answer(f"Max users: {max_users}")
```

### Pattern: Event-Driven Module

```python
async def on_load(self) -> None:
    await event_bus.subscribe("user.created", self.send_welcome)

async def send_welcome(self, data: dict) -> None:
    user_id = data.get("user_id")
    # Send welcome message
    pass
```

---

For API integration, see [API Documentation](API.md).

For architecture details, see [Architecture Documentation](ARCHITECTURE.md).

