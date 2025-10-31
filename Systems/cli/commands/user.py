"""
CLI commands for user management.
"""

import asyncio
from typing import Optional

import click

from Systems.core.database import get_session_factory
from Systems.core.database.models.user import UserRole
from Systems.core.logger import get_logger
from Systems.core.user.user_service import UserService

logger = get_logger(__name__)


@click.group(name="user")
def user_group() -> None:
    """User management commands."""
    pass


@user_group.command("add")
@click.argument("telegram_id", type=int)
@click.option("--username", help="Username")
@click.option("--full-name", help="Full name")
@click.option("--role", type=click.Choice(["user", "admin", "super_admin"]), default="user", help="User role")
def add_user(telegram_id: int, username: Optional[str], full_name: Optional[str], role: str) -> None:
    """
    Add a new user.
    
    Args:
        telegram_id: Telegram user ID
        username: Username (optional)
        full_name: Full name (optional)
        role: User role (user, admin, super_admin)
    
    Example:
        sdb user add 123456789 --username testuser --role admin
    """
    try:
        async def _add_user() -> None:
            async with get_session_factory()() as session:
                user_service = UserService(session)
                
                user = await user_service.get_or_create_user(
                    telegram_id=telegram_id,
                    username=username or f"user_{telegram_id}",
                    full_name=full_name,
                    role=UserRole(role),
                )
                
                await session.commit()
                
                click.echo(f"✓ User added/updated: {user.telegram_id} ({user.username})")
                logger.info(f"User added via CLI: {user.telegram_id}")
        
        asyncio.run(_add_user())
        
    except Exception as e:
        logger.error(f"Failed to add user: {e}", exc_info=True)
        click.echo(f"Error: {str(e)}", err=True)
        click.get_current_context().exit(1)


@user_group.command("role")
@click.argument("telegram_id", type=int)
@click.argument("role", type=click.Choice(["user", "admin", "super_admin"]))
def change_role(telegram_id: int, role: str) -> None:
    """
    Change user role.
    
    Args:
        telegram_id: Telegram user ID
        role: New role (user, admin, super_admin)
    
    Example:
        sdb user role 123456789 admin
    """
    try:
        async def _change_role() -> None:
            async with get_session_factory()() as session:
                user_service = UserService(session)
                
                user = await user_service.get_user(telegram_id)
                if not user:
                    click.echo(f"Error: User {telegram_id} not found", err=True)
                    click.get_current_context().exit(1)
                
                await user_service.change_user_role(telegram_id, UserRole(role))
                await session.commit()
                
                click.echo(f"✓ Role changed for user {telegram_id} to {role}")
                logger.info(f"User role changed via CLI: {telegram_id} -> {role}")
        
        asyncio.run(_change_role())
        
    except Exception as e:
        logger.error(f"Failed to change role: {e}", exc_info=True)
        click.echo(f"Error: {str(e)}", err=True)
        click.get_current_context().exit(1)


@user_group.command("permissions")
@click.argument("telegram_id", type=int)
def show_permissions(telegram_id: int) -> None:
    """
    Show user permissions.
    
    Args:
        telegram_id: Telegram user ID
    
    Example:
        sdb user permissions 123456789
    """
    try:
        async def _show_permissions() -> None:
            async with get_session_factory()() as session:
                user_service = UserService(session)
                
                user = await user_service.get_user(telegram_id)
                if not user:
                    click.echo(f"Error: User {telegram_id} not found", err=True)
                    click.get_current_context().exit(1)
                
                permissions = await user_service.get_user_permissions(telegram_id)
                
                click.echo(f"User: {user.username} ({user.telegram_id})")
                click.echo(f"Role: {user.role.value}")
                click.echo(f"Active: {user.is_active}")
                click.echo("")
                click.echo(f"Permissions ({len(permissions)}):")
                
                if permissions:
                    for perm in permissions:
                        click.echo(f"  - {perm}")
                else:
                    click.echo("  (no custom permissions)")
        
        asyncio.run(_show_permissions())
        
    except Exception as e:
        logger.error(f"Failed to show permissions: {e}", exc_info=True)
        click.echo(f"Error: {str(e)}", err=True)
        click.get_current_context().exit(1)


@user_group.command("list")
@click.option("--role", type=click.Choice(["user", "admin", "super_admin"]), help="Filter by role")
@click.option("--limit", type=int, default=100, help="Maximum number of users to show")
def list_users(role: Optional[str], limit: int) -> None:
    """
    List all users.
    
    Args:
        role: Filter by role (optional)
        limit: Maximum number of users to show
    
    Example:
        sdb user list
        sdb user list --role admin
        sdb user list --limit 50
    """
    try:
        async def _list_users() -> None:
            async with get_session_factory()() as session:
                user_service = UserService(session)
                
                if role:
                    users = await user_service.list_users_by_role(UserRole(role), limit=limit)
                else:
                    users = await user_service.list_users(limit=limit)
                
                if not users:
                    click.echo("No users found")
                    return
                
                click.echo(f"Users ({len(users)}):")
                click.echo("")
                click.echo(f"{'ID':<12} {'Username':<20} {'Role':<12} {'Status':<8}")
                click.echo("-" * 60)
                
                for user in users:
                    status = "Active" if user.is_active else "Inactive"
                    click.echo(f"{user.telegram_id:<12} {user.username:<20} {user.role.value:<12} {status:<8}")
        
        asyncio.run(_list_users())
        
    except Exception as e:
        logger.error(f"Failed to list users: {e}", exc_info=True)
        click.echo(f"Error: {str(e)}", err=True)
        click.get_current_context().exit(1)

