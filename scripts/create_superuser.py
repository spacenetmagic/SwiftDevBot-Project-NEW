#!/usr/bin/env python3
"""
Create super administrator user script.

Prompts for Telegram ID and creates super admin user.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from Systems.core.database import get_session_factory
from Systems.core.database.models.user import User, UserRole
from Systems.core.database.repositories.user_repository import UserRepository
from Systems.core.logger import get_logger
from Systems.core.utils.config import get_config
import click


logger = get_logger(__name__)


async def create_superuser(
    telegram_id: int,
    username: str | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
) -> User:
    """
    Create super administrator user.
    
    Args:
        telegram_id: Telegram user ID
        username: Telegram username (optional)
        first_name: First name (optional)
        last_name: Last name (optional)
        
    Returns:
        Created user object
    """
    async with get_session_factory()() as session:
        user_repo = UserRepository(session)
        
        # Check if user already exists
        existing_user = await user_repo.get_by_id(telegram_id)
        
        if existing_user:
            logger.info(f"User {telegram_id} already exists")
            
            if click.confirm("Update to super_admin?"):
                # Update to super_admin
                user = await user_repo.update(
                    telegram_id,
                    {
                        "role": UserRole.SUPER_ADMIN,
                        "is_active": True,
                    }
                )
                await session.commit()
                logger.info(f"✓ User {telegram_id} updated to super_admin")
                return user
            else:
                logger.info("Cancelled")
                return existing_user
        
        # Create new super_admin user
        user_data = {
            "telegram_id": telegram_id,
            "username": username or f"admin_{telegram_id}",
            "first_name": first_name or "Super",
            "last_name": last_name or "Admin",
            "role": UserRole.SUPER_ADMIN,
            "is_active": True,
        }
        
        user = await user_repo.create(user_data)
        await session.commit()
        
        logger.info(f"✓ Super admin user created: {telegram_id}")
        return user


async def list_superusers() -> list[User]:
    """
    List all super admin users.
    
    Returns:
        List of super admin users
    """
    async with get_session_factory()() as session:
        user_repo = UserRepository(session)
        
        users = await user_repo.get_by_role(UserRole.SUPER_ADMIN)
        
        return users


@click.command()
@click.option("--telegram-id", type=int, help="Telegram user ID")
@click.option("--username", type=str, help="Telegram username")
@click.option("--first-name", type=str, help="First name")
@click.option("--last-name", type=str, help="Last name")
@click.option("--list", "list_users", is_flag=True, help="List all super admin users")
def main(
    telegram_id: int | None,
    username: str | None,
    first_name: str | None,
    last_name: str | None,
    list_users: bool,
) -> None:
    """
    Create super administrator user.
    
    If telegram_id is not provided, prompts for it.
    """
    if list_users:
        users = asyncio.run(list_superusers())
        if users:
            click.echo(f"\nSuper Admin Users ({len(users)}):")
            click.echo("-" * 60)
            for user in users:
                click.echo(f"  ID: {user.telegram_id}, Username: {user.username}, "
                         f"Active: {user.is_active}")
        else:
            click.echo("No super admin users found")
        return
    
    # Prompt for telegram_id if not provided
    if not telegram_id:
        telegram_id = click.prompt("Enter Telegram User ID", type=int)
    
    # Prompt for optional fields
    if not username:
        username = click.prompt("Enter Username (optional)", default="", show_default=False)
        username = username if username else None
    
    if not first_name:
        first_name = click.prompt("Enter First Name (optional)", default="Super", show_default=False)
    
    if not last_name:
        last_name = click.prompt("Enter Last Name (optional)", default="Admin", show_default=False)
    
    try:
        user = asyncio.run(create_superuser(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
        ))
        
        click.echo(f"\n✓ Super admin user created/updated:")
        click.echo(f"  Telegram ID: {user.telegram_id}")
        click.echo(f"  Username: {user.username}")
        click.echo(f"  Role: {user.role.value}")
        click.echo(f"  Active: {user.is_active}")
        
    except Exception as e:
        logger.error(f"Failed to create superuser: {e}", exc_info=True)
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

