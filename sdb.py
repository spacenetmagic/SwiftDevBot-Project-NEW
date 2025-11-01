#!/usr/bin/env python3
"""
SwiftDevBot CLI - Main entry point.

Usage:
    sdb module list
    sdb user add 123456789 --role admin
    sdb bot start
    sdb dev shell
    sdb backup create
"""

import sys
from pathlib import Path

import click

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from Systems.cli.commands.module import module_group
from Systems.cli.commands.user import user_group
from Systems.cli.commands.dev import dev_group
from Systems.cli.commands.backup import backup_group
from Systems.cli.commands.db import db_group
from Systems.cli.commands.bot import bot_group
from Systems.core.logger import get_logger

logger = get_logger(__name__)

__version__ = "1.0.0"


@click.group()
@click.version_option(version=__version__, prog_name="sdb")
def cli() -> None:
    """
    SwiftDevBot CLI - Command-line interface for SwiftDevBot.
    
    SwiftDevBot is a modular Telegram bot framework with web panel.
    
    Examples:
        sdb module list                    # List all modules
        sdb module install ./my_module     # Install a module
        sdb user add 123456789 --role admin  # Add a user
        sdb bot start                      # Start bot service
        sdb dev shell                      # Open Python shell
        sdb backup create                  # Create a backup
    """
    pass


# Register command groups
cli.add_command(module_group)
cli.add_command(user_group)
cli.add_command(dev_group)
cli.add_command(backup_group)
cli.add_command(db_group)
cli.add_command(bot_group)


def main() -> None:
    """
    Main entry point for CLI.
    
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        cli()
    except KeyboardInterrupt:
        click.echo("\nInterrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"CLI error: {e}", exc_info=True)
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
