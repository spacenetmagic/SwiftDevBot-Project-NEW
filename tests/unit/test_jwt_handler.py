"""
Unit tests for JWTHandler.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from Systems.web.auth.jwt_handler import JWTHandler
from Systems.core.utils.config import Config


@pytest.fixture
def jwt_handler():
    """Create JWTHandler instance."""
    with patch("Systems.web.auth.jwt_handler.get_config") as mock_config:
        config = Config(
            bot_token="test_token",
            bot_username="testbot",
            super_admin_id=123456789,
            jwt_secret="a" * 32,
        )
        mock_config.return_value = config
        
        handler = JWTHandler()
        yield handler


@pytest.mark.asyncio
async def test_create_access_token(jwt_handler: JWTHandler) -> None:
    """Test creating access token."""
    token = await jwt_handler.create_access_token(
        user_id=123456789,
        username="testuser",
        role="admin",
    )
    
    assert token is not None
    assert isinstance(token, str)
    assert len(token) > 0


@pytest.mark.asyncio
async def test_create_refresh_token(jwt_handler: JWTHandler) -> None:
    """Test creating refresh token."""
    token = await jwt_handler.create_refresh_token(user_id=123456789)
    
    assert token is not None
    assert isinstance(token, str)
    assert len(token) > 0


@pytest.mark.asyncio
async def test_verify_token_valid(jwt_handler: JWTHandler) -> None:
    """Test verifying valid token."""
    token = await jwt_handler.create_access_token(user_id=123456789)
    
    is_valid = await jwt_handler.verify_token(token)
    
    assert is_valid is True


@pytest.mark.asyncio
async def test_verify_token_invalid(jwt_handler: JWTHandler) -> None:
    """Test verifying invalid token."""
    is_valid = await jwt_handler.verify_token("invalid.token.here")
    
    assert is_valid is False


@pytest.mark.asyncio
async def test_decode_token(jwt_handler: JWTHandler) -> None:
    """Test decoding token."""
    token = await jwt_handler.create_access_token(
        user_id=123456789,
        username="testuser",
        role="admin",
    )
    
    payload = await jwt_handler.decode_token(token)
    
    assert payload["sub"] == "123456789"
    assert payload["type"] == "access"
    assert payload["username"] == "testuser"
    assert payload["role"] == "admin"
    assert "exp" in payload
    assert "iat" in payload


@pytest.mark.asyncio
async def test_decode_token_expired(jwt_handler: JWTHandler) -> None:
    """Test decoding expired token."""
    # Create token with very short expiration
    token = await jwt_handler.create_access_token(
        user_id=123456789,
        expires_in=timedelta(seconds=-1),  # Already expired
    )
    
    with pytest.raises(Exception):  # Should raise ExpiredSignatureError or InvalidTokenError
        await jwt_handler.decode_token(token)


@pytest.mark.asyncio
async def test_refresh_access_token(jwt_handler: JWTHandler) -> None:
    """Test refreshing access token."""
    refresh_token = await jwt_handler.create_refresh_token(user_id=123456789)
    
    new_access_token = await jwt_handler.refresh_access_token(refresh_token)
    
    assert new_access_token is not None
    assert isinstance(new_access_token, str)
    
    # Verify new token
    payload = await jwt_handler.decode_token(new_access_token)
    assert payload["type"] == "access"
    assert payload["sub"] == "123456789"


@pytest.mark.asyncio
async def test_refresh_access_token_invalid_type(jwt_handler: JWTHandler) -> None:
    """Test refreshing with access token instead of refresh token."""
    access_token = await jwt_handler.create_access_token(user_id=123456789)
    
    with pytest.raises(Exception):  # Should raise InvalidTokenError
        await jwt_handler.refresh_access_token(access_token)


@pytest.mark.asyncio
async def test_token_expiration_times(jwt_handler: JWTHandler) -> None:
    """Test token expiration times."""
    access_token = await jwt_handler.create_access_token(user_id=123456789)
    refresh_token = await jwt_handler.create_refresh_token(user_id=123456789)
    
    access_payload = await jwt_handler.decode_token(access_token)
    refresh_payload = await jwt_handler.decode_token(refresh_token)
    
    access_exp = datetime.fromtimestamp(access_payload["exp"])
    refresh_exp = datetime.fromtimestamp(refresh_payload["exp"])
    now = datetime.utcnow()
    
    # Access token should expire in ~24 hours
    access_delta = access_exp - now
    assert timedelta(hours=23) < access_delta < timedelta(hours=25)
    
    # Refresh token should expire in ~7 days
    refresh_delta = refresh_exp - now
    assert timedelta(days=6) < refresh_delta < timedelta(days=8)

