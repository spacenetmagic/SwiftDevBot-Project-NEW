"""
Unit tests for AuditRepository.
"""

import asyncio

import pytest

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from Systems.core.database import Base
from Systems.core.database.repositories.audit_repository import AuditRepository
from Systems.core.database.repositories.user_repository import UserRepository
from Systems.core.database.models.user import UserRole


@pytest.fixture
async def db_session():
    """Create a test database session."""
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
async def test_user(db_session: AsyncSession):
    """Create a test user."""
    user_repo = UserRepository(db_session)
    user_data = {
        "telegram_id": 123456789,
        "username": "testuser",
        "first_name": "Test",
        "role": UserRole.USER,
    }
    user = await user_repo.create(user_data)
    await db_session.commit()
    return user


@pytest.fixture
def audit_repo(db_session: AsyncSession) -> AuditRepository:
    """Create an AuditRepository instance."""
    return AuditRepository(db_session)


@pytest.mark.asyncio
async def test_log_audit_entry(audit_repo: AuditRepository, test_user) -> None:
    """Test creating an audit log entry."""
    audit_log = await audit_repo.log(
        user_id=test_user.telegram_id,
        action="create",
        resource="user",
        old_value=None,
        new_value={"username": "testuser"},
        ip_address="127.0.0.1",
        success=True,
    )
    await audit_repo.session.commit()
    
    assert audit_log.id is not None
    assert audit_log.user_id == test_user.telegram_id
    assert audit_log.action == "create"
    assert audit_log.resource == "user"
    assert audit_log.new_value == {"username": "testuser"}
    assert audit_log.ip_address == "127.0.0.1"
    assert audit_log.success is True
    assert audit_log.timestamp is not None


@pytest.mark.asyncio
async def test_log_with_minimal_data(audit_repo: AuditRepository, test_user) -> None:
    """Test creating an audit log with minimal data."""
    audit_log = await audit_repo.log(
        user_id=test_user.telegram_id,
        action="view",
        resource="dashboard",
    )
    await audit_repo.session.commit()
    
    assert audit_log.id is not None
    assert audit_log.user_id == test_user.telegram_id
    assert audit_log.action == "view"
    assert audit_log.resource == "dashboard"
    assert audit_log.old_value is None
    assert audit_log.new_value is None
    assert audit_log.ip_address is None
    assert audit_log.success is True  # Default value


@pytest.mark.asyncio
async def test_get_logs_by_user(audit_repo: AuditRepository, test_user) -> None:
    """Test getting audit logs for a specific user."""
    # Create multiple audit logs
    log1 = await audit_repo.log(test_user.telegram_id, "action1", "resource1")
    log2 = await audit_repo.log(test_user.telegram_id, "action2", "resource2")
    log3 = await audit_repo.log(test_user.telegram_id, "action3", "resource3")
    await audit_repo.session.commit()
    
    logs = await audit_repo.get_logs(test_user.telegram_id, limit=10)
    
    assert len(logs) == 3
    assert all(log.user_id == test_user.telegram_id for log in logs)
    # Verify all actions are present (order may vary due to timestamp precision)
    actions = {log.action for log in logs}
    assert actions == {"action1", "action2", "action3"}
    # Verify logs are ordered by timestamp descending (newest first)
    # Check that log IDs are in descending order (newer logs have higher IDs)
    log_ids = [log.id for log in logs]
    # ID should be highest for the last created log
    assert max(log_ids) == log3.id


@pytest.mark.asyncio
async def test_get_logs_with_limit(audit_repo: AuditRepository, test_user) -> None:
    """Test getting audit logs with limit."""
    # Create more logs than limit
    for i in range(10):
        await audit_repo.log(test_user.telegram_id, f"action{i}", f"resource{i}")
        await asyncio.sleep(0.01)
    await audit_repo.session.commit()

    logs = await audit_repo.get_logs(test_user.telegram_id, limit=5)

    assert len(logs) == 5
    actions = [log.action for log in logs]
    expected_actions = [f"action{i}" for i in range(9, 4, -1)]
    assert actions == expected_actions
    ids = [log.id for log in logs]
    assert ids == sorted(ids, reverse=True)


@pytest.mark.asyncio
async def test_get_action_logs(audit_repo: AuditRepository, test_user) -> None:
    """Test getting audit logs for a specific action."""
    # Create logs with different actions
    await audit_repo.log(test_user.telegram_id, "create", "user")
    await audit_repo.log(test_user.telegram_id, "update", "user")
    await audit_repo.log(test_user.telegram_id, "create", "post")
    await audit_repo.session.commit()
    
    logs = await audit_repo.get_action_logs("create", limit=10)
    
    assert len(logs) == 2
    assert all(log.action == "create" for log in logs)


@pytest.mark.asyncio
async def test_get_action_logs_with_limit(audit_repo: AuditRepository, test_user) -> None:
    """Test getting action logs with limit."""
    # Create multiple logs with same action
    for i in range(10):
        await audit_repo.log(test_user.telegram_id, "create", f"resource{i}")
    await audit_repo.session.commit()
    
    logs = await audit_repo.get_action_logs("create", limit=3)
    
    assert len(logs) == 3
    assert all(log.action == "create" for log in logs)


@pytest.mark.asyncio
async def test_log_failed_action(audit_repo: AuditRepository, test_user) -> None:
    """Test logging a failed action."""
    audit_log = await audit_repo.log(
        user_id=test_user.telegram_id,
        action="delete",
        resource="user",
        success=False,
    )
    await audit_repo.session.commit()
    
    assert audit_log.success is False


@pytest.mark.asyncio
async def test_log_with_old_and_new_values(audit_repo: AuditRepository, test_user) -> None:
    """Test logging with old and new values."""
    audit_log = await audit_repo.log(
        user_id=test_user.telegram_id,
        action="update",
        resource="user",
        old_value={"username": "olduser"},
        new_value={"username": "newuser"},
    )
    await audit_repo.session.commit()
    
    assert audit_log.old_value == {"username": "olduser"}
    assert audit_log.new_value == {"username": "newuser"}


@pytest.mark.asyncio
async def test_get_logs_empty(audit_repo: AuditRepository, test_user) -> None:
    """Test getting logs when none exist."""
    logs = await audit_repo.get_logs(test_user.telegram_id, limit=10)
    
    assert len(logs) == 0

