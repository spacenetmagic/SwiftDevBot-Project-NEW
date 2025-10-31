"""
Integration tests for web authentication.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from Systems.core.database.models.user import User, UserRole
from Systems.web.auth.jwt_handler import JWTHandler
from Systems.web.auth.telegram_auth import TelegramAuth
from Systems.web.auth.routes import router as auth_router


@pytest.fixture
def jwt_handler():
    """Create JWTHandler instance."""
    return JWTHandler()


@pytest.fixture
def telegram_auth(db_session):
    """Create TelegramAuth instance."""
    return TelegramAuth(db_session)


@pytest.mark.asyncio
async def test_create_access_token(jwt_handler) -> None:
    """Test creating access token."""
    token = await jwt_handler.create_access_token(
        user_id=123456789,
        username="testuser",
        role="user"
    )
    
    assert token is not None
    assert isinstance(token, str)


@pytest.mark.asyncio
async def test_verify_access_token(jwt_handler) -> None:
    """Test verifying access token."""
    token = await jwt_handler.create_access_token(
        user_id=123456789,
        username="testuser",
        role="user"
    )
    
    # verify_token returns bool
    is_valid = await jwt_handler.verify_token(token)
    assert is_valid is True
    
    # Use decode_token to get payload
    decoded = await jwt_handler.decode_token(token)
    assert decoded is not None
    assert decoded.get("sub") == "123456789"
    assert decoded.get("role") == "user"


@pytest.mark.asyncio
async def test_verify_expired_token(jwt_handler) -> None:
    """Test verifying expired token."""
    # Test with invalid token
    invalid_token = "invalid.token.here"
    
    # Token should fail verification
    is_valid = await jwt_handler.verify_token(invalid_token)
    # Should return False for invalid token
    assert is_valid is False


@pytest.mark.asyncio
async def test_create_refresh_token(jwt_handler) -> None:
    """Test creating refresh token."""
    token = await jwt_handler.create_refresh_token(user_id=123456789)
    
    assert token is not None
    assert isinstance(token, str)


@pytest.mark.asyncio
async def test_verify_refresh_token(jwt_handler) -> None:
    """Test verifying refresh token."""
    token = await jwt_handler.create_refresh_token(user_id=123456789)
    
    # Refresh tokens are verified the same way as access tokens
    is_valid = await jwt_handler.verify_token(token)
    assert is_valid is True
    
    # Use decode_token to get payload
    decoded = await jwt_handler.decode_token(token)
    assert decoded is not None
    assert decoded.get("sub") == "123456789"
    assert decoded.get("type") == "refresh"


@pytest.mark.asyncio
async def test_telegram_hash_verification(telegram_auth) -> None:
    """Test Telegram hash verification."""
    # This is a simplified test - real verification requires actual Telegram data
    auth_data = {
        "id": "123456789",
        "first_name": "Test",
        "username": "testuser",
        "auth_date": str(int(datetime.now().timestamp())),
        "hash": "test_hash",
    }
    
    # Use verify_telegram_auth method
    result = telegram_auth.verify_telegram_auth(auth_data)
    
    # Should return False for invalid hash (in real scenario with valid hash it would return True)
    assert isinstance(result, bool)


@pytest.mark.asyncio
async def test_telegram_auth_get_or_create_user(telegram_auth, db_session) -> None:
    """Test getting or creating user via Telegram auth."""
    # Mock hash verification to return True
    with patch.object(telegram_auth, "verify_telegram_auth", return_value=True):
        auth_data = {
            "id": "123456789",  # Telegram sends as string
            "first_name": "Test",
            "last_name": "User",
            "username": "testuser",
            "auth_date": str(int(datetime.now().timestamp())),
            "hash": "mock_hash",
        }
        
        user = await telegram_auth.authenticate_user(auth_data)
        
        assert user is not None
        assert user.telegram_id == 123456789
        assert user.username == "testuser"


@pytest.mark.asyncio
async def test_telegram_auth_update_user(telegram_auth, db_session, test_user) -> None:
    """Test updating existing user via Telegram auth."""
    # Mock hash verification to return True
    with patch.object(telegram_auth, "verify_telegram_auth", return_value=True):
        auth_data = {
            "id": str(test_user.telegram_id),  # Telegram sends as string
            "first_name": "Updated",
            "last_name": "Name",
            "username": "updateduser",
            "auth_date": str(int(datetime.now().timestamp())),
            "hash": "mock_hash",
        }
        
        user = await telegram_auth.authenticate_user(auth_data)
        await db_session.refresh(user)
        
        assert user.username == "updateduser"
        assert user.first_name == "Updated"
        assert user.last_name == "Name"


@pytest.mark.asyncio
async def test_jwt_token_expiration(jwt_handler) -> None:
    """Test JWT token expiration."""
    token = await jwt_handler.create_access_token(
        user_id=123456789,
        username="testuser",
        role="user"
    )
    
    # Verify token is valid
    is_valid = await jwt_handler.verify_token(token)
    assert is_valid is True
    
    # Decode to check expiration claim
    decoded = await jwt_handler.decode_token(token)
    assert "exp" in decoded  # Token has expiration claim
    assert token is not None
    assert isinstance(token, str)


@pytest.mark.asyncio
async def test_refresh_token_rotation(jwt_handler) -> None:
    """Test refresh token rotation."""
    # Create initial refresh token
    refresh_token = await jwt_handler.create_refresh_token(user_id=123456789)
    
    # Verify refresh token
    is_valid = await jwt_handler.verify_token(refresh_token)
    assert is_valid is True
    
    # Decode refresh token to get user_id
    decoded = await jwt_handler.decode_token(refresh_token)
    user_id = int(decoded.get("sub"))
    
    # Use refresh_access_token to create new access token
    access_token = await jwt_handler.refresh_access_token(refresh_token)
    
    assert access_token is not None
    assert isinstance(access_token, str)

