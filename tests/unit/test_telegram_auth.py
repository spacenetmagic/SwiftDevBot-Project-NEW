"""
Unit tests for TelegramAuth.
"""

import hmac
import hashlib
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from Systems.web.auth.telegram_auth import TelegramAuth
from Systems.core.database.models.user import User, UserRole


@pytest.fixture
def mock_session():
    """Create mock database session."""
    session = AsyncMock()
    session.commit = AsyncMock()
    return session


@pytest.fixture
def telegram_auth(mock_session):
    """Create TelegramAuth instance."""
    with patch("Systems.web.auth.telegram_auth.get_config") as mock_config:
        config = MagicMock()
        config.bot_token = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
        mock_config.return_value = config
        
        auth = TelegramAuth(mock_session)
        return auth


def create_telegram_auth_data(bot_token: str, user_id: int = 123456789) -> dict:
    """
    Create valid Telegram auth data for testing.
    
    Args:
        bot_token: Bot token
        user_id: User ID
        
    Returns:
        Dictionary with Telegram auth data
    """
    auth_date = int(datetime.utcnow().timestamp())
    
    auth_data = {
        "id": user_id,
        "first_name": "Test",
        "username": "testuser",
        "auth_date": auth_date,
    }
    
    # Calculate hash
    data_check_string_parts = []
    for key in sorted(auth_data.keys()):
        if key != "hash":
            value = auth_data[key]
            data_check_string_parts.append(f"{key}={value}")
    
    data_check_string = "\n".join(data_check_string_parts)
    
    secret_key = hmac.new(
        "WebAppData".encode("utf-8"),
        bot_token.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    
    calculated_hash = hmac.new(
        secret_key,
        data_check_string.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    
    auth_data["hash"] = calculated_hash
    
    return auth_data


@pytest.mark.asyncio
async def test_verify_telegram_auth_valid(telegram_auth: TelegramAuth) -> None:
    """Test verifying valid Telegram auth data."""
    bot_token = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
    auth_data = create_telegram_auth_data(bot_token)
    
    result = telegram_auth.verify_telegram_auth(auth_data)
    
    assert result is True


@pytest.mark.asyncio
async def test_verify_telegram_auth_invalid_hash(telegram_auth: TelegramAuth) -> None:
    """Test verifying Telegram auth with invalid hash."""
    bot_token = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
    auth_data = create_telegram_auth_data(bot_token)
    auth_data["hash"] = "invalid_hash"
    
    result = telegram_auth.verify_telegram_auth(auth_data)
    
    assert result is False


@pytest.mark.asyncio
async def test_verify_telegram_auth_expired(telegram_auth: TelegramAuth) -> None:
    """Test verifying expired Telegram auth data."""
    bot_token = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
    auth_data = create_telegram_auth_data(bot_token)
    
    # Make auth_date old (more than 24 hours)
    old_timestamp = int((datetime.utcnow() - timedelta(hours=25)).timestamp())
    auth_data["auth_date"] = old_timestamp
    
    # Recalculate hash with new timestamp
    data_check_string_parts = []
    for key in sorted(auth_data.keys()):
        if key != "hash":
            value = auth_data[key]
            data_check_string_parts.append(f"{key}={value}")
    
    data_check_string = "\n".join(data_check_string_parts)
    secret_key = hmac.new(
        "WebAppData".encode("utf-8"),
        bot_token.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    auth_data["hash"] = hmac.new(
        secret_key,
        data_check_string.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    
    result = telegram_auth.verify_telegram_auth(auth_data)
    
    assert result is False


@pytest.mark.asyncio
async def test_verify_telegram_auth_missing_fields(telegram_auth: TelegramAuth) -> None:
    """Test verifying Telegram auth with missing fields."""
    auth_data = {"id": 123456789}  # Missing required fields
    
    result = telegram_auth.verify_telegram_auth(auth_data)
    
    assert result is False


@pytest.mark.asyncio
async def test_authenticate_user_new_user(telegram_auth: TelegramAuth, mock_session) -> None:
    """Test authenticating a new user."""
    bot_token = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
    auth_data = create_telegram_auth_data(bot_token, user_id=999999999)
    
    # Mock user repository
    telegram_auth.user_repo.get_by_id = AsyncMock(return_value=None)
    telegram_auth.user_repo.create = AsyncMock(return_value=MagicMock(
        telegram_id=999999999,
        username="testuser",
        first_name="Test",
        role=UserRole.USER,
    ))
    
    with patch("Systems.web.auth.telegram_auth.get_config") as mock_config:
        config = MagicMock()
        config.super_admin_id = 123456789  # Different from user_id
        mock_config.return_value = config
        
        user = await telegram_auth.authenticate_user(auth_data)
        
        assert user is not None
        telegram_auth.user_repo.create.assert_called_once()


@pytest.mark.asyncio
async def test_authenticate_user_existing_user(telegram_auth: TelegramAuth, mock_session) -> None:
    """Test authenticating an existing user."""
    bot_token = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
    auth_data = create_telegram_auth_data(bot_token, user_id=123456789)
    
    # Mock existing user
    existing_user = MagicMock(
        telegram_id=123456789,
        username="olduser",
        first_name="Old",
        role=UserRole.USER,
    )
    
    telegram_auth.user_repo.get_by_id = AsyncMock(return_value=existing_user)
    telegram_auth.user_repo.update = AsyncMock(return_value=existing_user)
    
    user = await telegram_auth.authenticate_user(auth_data)
    
    assert user is not None
    telegram_auth.user_repo.update.assert_called_once()


@pytest.mark.asyncio
async def test_authenticate_user_invalid_data(telegram_auth: TelegramAuth) -> None:
    """Test authenticating with invalid auth data."""
    auth_data = {"id": 123456789, "hash": "invalid"}
    
    with pytest.raises(ValueError, match="Invalid Telegram authentication"):
        await telegram_auth.authenticate_user(auth_data)

