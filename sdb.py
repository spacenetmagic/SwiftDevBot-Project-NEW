#!/usr/bin/env python3
"""
SwiftDevBot CLI - Main entry point with Typer + Rich.

Usage:
    sdb module list
    sdb user add 123456789 --role admin
    sdb bot start
    sdb dev shell
    sdb backup create

For shell completion, run:
    sdb --install-completion [bash|zsh|fish|powershell]
"""

import sys
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import apps directly (not through __init__ to avoid circular imports)
from Systems.cli.commands.bot import app as bot_app
from Systems.cli.commands.module import app as module_app
from Systems.cli.commands.user import app as user_app
from Systems.cli.commands.dev import app as dev_app
from Systems.cli.commands.backup import app as backup_app
from Systems.cli.commands.db import app as db_app
from Systems.core.logger import get_logger

logger = get_logger(__name__)

__version__ = "1.0.0"

# Create main Typer app
app = typer.Typer(
    name="sdb",
    help="SwiftDevBot CLI - Command-line interface for SwiftDevBot",
    add_completion=True,  # Enable shell completion
    rich_markup_mode="rich",
)

# Create console for Rich output
console = Console()


@app.command("version", help="Show version information")
def version() -> None:
    """Show version information."""
    console.print(Panel.fit(
        f"[bold blue]SwiftDevBot[/bold blue] [dim]v{__version__}[/dim]\n\n"
        "[dim]Modular Telegram Bot Framework with Web Panel[/dim]",
        title="Version",
        border_style="blue"
    ))


# Add subcommands
app.add_typer(bot_app, name="bot", help="Bot management commands")
app.add_typer(module_app, name="module", help="Module management commands")
app.add_typer(user_app, name="user", help="User management commands")
app.add_typer(dev_app, name="dev", help="Development tools")
app.add_typer(backup_app, name="backup", help="Backup management")
app.add_typer(db_app, name="db", help="Database management")


def callback(ctx: typer.Context) -> None:
    """Global callback for CLI."""
    if ctx.invoked_subcommand is None:
        # Show help if no command specified
        console.print(Panel.fit(
            "[bold blue]SwiftDevBot[/bold blue] [dim]CLI[/dim]\n\n"
            "Use [cyan]sdb --help[/cyan] to see available commands.\n"
            "For shell completion: [cyan]sdb --install-completion [bash|zsh|fish|powershell][/cyan]",
            title="Welcome",
            border_style="blue"
        ))


# Set callback
app.callback()(callback)


def main() -> None:
    """
    Main entry point for CLI.
    
    For shell completion, run:
        sdb --install-completion [bash|zsh|fish|powershell]
    """
    try:
        app()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(130)
    except Exception as e:
        logger.error(f"CLI error: {e}", exc_info=True)
        console.print(f"[red]Error:[/red] {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
