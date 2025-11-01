"""
CLI commands for user management with Typer + Rich.
TODO: Migrate full functionality from Click to Typer.
"""

import typer
from rich.console import Console

console = Console()
app = typer.Typer(name="user", help="User management commands", rich_markup_mode="rich")

@app.command("list")
def list_users() -> None:
    """List all users."""
    console.print("[yellow]⚠ User management commands are being migrated to Typer.[/yellow]")
    console.print("[dim]This command will be fully implemented soon.[/dim]")

# TODO: Migrate remaining commands from Click
