"""
Unit tests for UserRepository.
"""

import pytest
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from Systems.core.database import Base
from Systems.core.database.models.user import User, UserRole
from Systems.core.database.repositories.user_repository import UserRepository


@pytest.fixture
async def db_session():
    """Create a test database session."""
    # Use in-memory SQLite for testing
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session_maker = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session_maker() as session:
        yield session
    
    await engine.dispose()


@pytest.fixture
def user_repo(db_session: AsyncSession) -> UserRepository:
    """Create a UserRepository instance."""
    return UserRepository(db_session)


@pytest.mark.asyncio
async def test_create_user(user_repo: UserRepository) -> None:
    """Test creating a new user."""
    user_data = {
        "telegram_id": 123456789,
        "username": "testuser",
        "first_name": "Test",
        "last_name": "User",
        "role": UserRole.USER,
    }
    
    user = await user_repo.create(user_data)
    
    assert user.telegram_id == 123456789
    assert user.username == "testuser"
    assert user.first_name == "Test"
    assert user.last_name == "User"
    assert user.role == UserRole.USER
    assert user.is_active is True
    assert user.custom_permissions == []


@pytest.mark.asyncio
async def test_create_duplicate_user(user_repo: UserRepository) -> None:
    """Test creating a duplicate user raises ValueError."""
    user_data = {
        "telegram_id": 123456789,
        "username": "testuser",
        "first_name": "Test",
        "role": UserRole.USER,
    }
    
    await user_repo.create(user_data)
    
    # Try to create duplicate
    with pytest.raises(ValueError, match="already exists"):
        await user_repo.create(user_data)


@pytest.mark.asyncio
async def test_get_by_id_existing(user_repo: UserRepository) -> None:
    """Test getting an existing user by ID."""
    user_data = {
        "telegram_id": 123456789,
        "username": "testuser",
        "first_name": "Test",
        "role": UserRole.USER,
    }
    
    created = await user_repo.create(user_data)
    await user_repo.session.commit()
    
    found = await user_repo.get_by_id(123456789)
    
    assert found is not None
    assert found.telegram_id == created.telegram_id
    assert found.username == created.username


@pytest.mark.asyncio
async def test_get_by_id_nonexistent(user_repo: UserRepository) -> None:
    """Test getting a non-existent user returns None."""
    found = await user_repo.get_by_id(999999999)
    
    assert found is None


@pytest.mark.asyncio
async def test_update_user(user_repo: UserRepository) -> None:
    """Test updating a user."""
    user_data = {
        "telegram_id": 123456789,
        "username": "testuser",
        "first_name": "Test",
        "role": UserRole.USER,
    }
    
    await user_repo.create(user_data)
    await user_repo.session.commit()
    
    updated = await user_repo.update(123456789, {"username": "newuser", "role": UserRole.ADMIN})
    await user_repo.session.commit()
    
    assert updated is not None
    assert updated.username == "newuser"
    assert updated.role == UserRole.ADMIN


@pytest.mark.asyncio
async def test_update_nonexistent_user(user_repo: UserRepository) -> None:
    """Test updating a non-existent user returns None."""
    updated = await user_repo.update(999999999, {"username": "newuser"})
    
    assert updated is None


@pytest.mark.asyncio
async def test_get_all(user_repo: UserRepository) -> None:
    """Test getting all users with pagination."""
    # Create multiple users
    for i in range(5):
        user_data = {
            "telegram_id": 100000000 + i,
            "username": f"user{i}",
            "first_name": f"User{i}",
            "role": UserRole.USER,
        }
        await user_repo.create(user_data)
    
    await user_repo.session.commit()
    
    users = await user_repo.get_all(skip=0, limit=10)
    
    assert len(users) == 5


@pytest.mark.asyncio
async def test_get_all_pagination(user_repo: UserRepository) -> None:
    """Test pagination in get_all."""
    # Create multiple users
    for i in range(10):
        user_data = {
            "telegram_id": 100000000 + i,
            "username": f"user{i}",
            "first_name": f"User{i}",
            "role": UserRole.USER,
        }
        await user_repo.create(user_data)
    
    await user_repo.session.commit()
    
    # Get first page
    users1 = await user_repo.get_all(skip=0, limit=5)
    assert len(users1) == 5
    
    # Get second page
    users2 = await user_repo.get_all(skip=5, limit=5)
    assert len(users2) == 5
    assert users1[0].telegram_id != users2[0].telegram_id


@pytest.mark.asyncio
async def test_delete_user(user_repo: UserRepository) -> None:
    """Test deleting a user."""
    user_data = {
        "telegram_id": 123456789,
        "username": "testuser",
        "first_name": "Test",
        "role": UserRole.USER,
    }
    
    await user_repo.create(user_data)
    await user_repo.session.commit()
    
    deleted = await user_repo.delete(123456789)
    await user_repo.session.commit()
    
    assert deleted is True
    
    found = await user_repo.get_by_id(123456789)
    assert found is None


@pytest.mark.asyncio
async def test_delete_nonexistent_user(user_repo: UserRepository) -> None:
    """Test deleting a non-existent user returns False."""
    deleted = await user_repo.delete(999999999)
    
    assert deleted is False


@pytest.mark.asyncio
async def test_get_by_role(user_repo: UserRepository) -> None:
    """Test getting users by role."""
    # Create users with different roles
    await user_repo.create({
        "telegram_id": 1001,
        "username": "admin1",
        "first_name": "Admin1",
        "role": UserRole.ADMIN,
    })
    await user_repo.create({
        "telegram_id": 1002,
        "username": "admin2",
        "first_name": "Admin2",
        "role": UserRole.ADMIN,
    })
    await user_repo.create({
        "telegram_id": 2001,
        "username": "user1",
        "first_name": "User1",
        "role": UserRole.USER,
    })
    
    await user_repo.session.commit()
    
    admins = await user_repo.get_by_role(UserRole.ADMIN)
    
    assert len(admins) == 2
    assert all(user.role == UserRole.ADMIN for user in admins)


@pytest.mark.asyncio
async def test_count_all(user_repo: UserRepository) -> None:
    """Test counting all users."""
    # Create multiple users
    for i in range(5):
        user_data = {
            "telegram_id": 100000000 + i,
            "username": f"user{i}",
            "first_name": f"User{i}",
            "role": UserRole.USER,
        }
        await user_repo.create(user_data)
    
    await user_repo.session.commit()
    
    count = await user_repo.count_all()
    
    assert count == 5


@pytest.mark.asyncio
async def test_count_all_empty(user_repo: UserRepository) -> None:
    """Test counting when no users exist."""
    count = await user_repo.count_all()
    
    assert count == 0

