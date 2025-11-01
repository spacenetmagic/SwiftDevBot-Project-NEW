"""
CLI commands package (Typer + Rich).
"""

from Systems.cli.commands.module import app as module_app
from Systems.cli.commands.user import app as user_app
from Systems.cli.commands.dev import app as dev_app
from Systems.cli.commands.backup import app as backup_app
from Systems.cli.commands.db import app as db_app
from Systems.cli.commands.bot import app as bot_app

__all__ = [
    "module_app",
    "user_app",
    "dev_app",
    "backup_app",
    "db_app",
    "bot_app",
]

