"""
Unit tests for configuration module.
"""

import os
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from Systems.core.utils.config import Config, get_config, reload_config


class TestConfig:
    """Test cases for Config class."""
    
    def test_config_validation_bot_token_empty(self) -> None:
        """Test that empty bot token raises ValueError."""
        with pytest.raises(ValueError, match="BOT_TOKEN cannot be empty"):
            Config(
                bot_token="",
                bot_username="testbot",
                super_admin_id=123456789,
                db_password="testpass",
                jwt_secret="a" * 32
            )
    
    def test_config_validation_bot_token_whitespace(self) -> None:
        """Test that whitespace-only bot token raises ValueError."""
        with pytest.raises(ValueError, match="BOT_TOKEN cannot be empty"):
            Config(
                bot_token="   ",
                bot_username="testbot",
                super_admin_id=123456789,
                db_password="testpass",
                jwt_secret="a" * 32
            )
    
    def test_config_validation_bot_token_stripped(self) -> None:
        """Test that bot token is properly stripped."""
        config = Config(
            bot_token="  test_token  ",
            bot_username="testbot",
            super_admin_id=123456789,
            db_password="testpass",
            jwt_secret="a" * 32
        )
        assert config.bot_token == "test_token"
    
    def test_config_validation_bot_username_at_removed(self) -> None:
        """Test that @ is removed from bot username."""
        config = Config(
            bot_token="test_token",
            bot_username="@testbot",
            super_admin_id=123456789,
            db_password="testpass",
            jwt_secret="a" * 32
        )
        assert config.bot_username == "testbot"
    
    def test_config_validation_bot_username_stripped(self) -> None:
        """Test that bot username is properly stripped."""
        config = Config(
            bot_token="test_token",
            bot_username="  testbot  ",
            super_admin_id=123456789,
            db_password="testpass",
            jwt_secret="a" * 32
        )
        assert config.bot_username == "testbot"
    
    def test_config_validation_super_admin_id_negative(self) -> None:
        """Test that negative super admin ID raises ValueError."""
        with pytest.raises(ValueError, match="SUPER_ADMIN_ID must be a positive integer"):
            Config(
                bot_token="test_token",
                bot_username="testbot",
                super_admin_id=-1,
                db_password="testpass",
                jwt_secret="a" * 32
            )
    
    def test_config_validation_super_admin_id_zero(self) -> None:
        """Test that zero super admin ID raises ValueError."""
        with pytest.raises(ValueError, match="SUPER_ADMIN_ID must be a positive integer"):
            Config(
                bot_token="test_token",
                bot_username="testbot",
                super_admin_id=0,
                db_password="testpass",
                jwt_secret="a" * 32
            )
    
    def test_config_validation_db_port_invalid_low(self) -> None:
        """Test that DB port below 1 raises ValueError."""
        with pytest.raises(ValueError, match="DB_PORT must be between 1 and 65535"):
            Config(
                bot_token="test_token",
                bot_username="testbot",
                super_admin_id=123456789,
                db_password="testpass",
                jwt_secret="a" * 32,
                db_port=0
            )
    
    def test_config_validation_db_port_invalid_high(self) -> None:
        """Test that DB port above 65535 raises ValueError."""
        with pytest.raises(ValueError, match="DB_PORT must be between 1 and 65535"):
            Config(
                bot_token="test_token",
                bot_username="testbot",
                super_admin_id=123456789,
                db_password="testpass",
                jwt_secret="a" * 32,
                db_port=65536
            )
    
    def test_config_validation_redis_port_invalid_low(self) -> None:
        """Test that Redis port below 1 raises ValueError."""
        with pytest.raises(ValueError, match="REDIS_PORT must be between 1 and 65535"):
            Config(
                bot_token="test_token",
                bot_username="testbot",
                super_admin_id=123456789,
                db_password="testpass",
                jwt_secret="a" * 32,
                redis_port=0
            )
    
    def test_config_validation_redis_port_invalid_high(self) -> None:
        """Test that Redis port above 65535 raises ValueError."""
        with pytest.raises(ValueError, match="REDIS_PORT must be between 1 and 65535"):
            Config(
                bot_token="test_token",
                bot_username="testbot",
                super_admin_id=123456789,
                db_password="testpass",
                jwt_secret="a" * 32,
                redis_port=65536
            )
    
    def test_config_validation_jwt_secret_too_short(self) -> None:
        """Test that JWT secret shorter than 32 chars raises ValueError."""
        with pytest.raises(ValueError, match="JWT_SECRET must be at least 32 characters long"):
            Config(
                bot_token="test_token",
                bot_username="testbot",
                super_admin_id=123456789,
                db_password="testpass",
                jwt_secret="short"
            )
    
    def test_config_validation_jwt_secret_exact_32(self) -> None:
        """Test that JWT secret of exactly 32 chars is valid."""
        config = Config(
            bot_token="test_token",
            bot_username="testbot",
            super_admin_id=123456789,
            db_password="testpass",
            jwt_secret="a" * 32
        )
        assert len(config.jwt_secret) == 32
    
    def test_config_validation_log_level_invalid(self) -> None:
        """Test that invalid log level raises ValueError."""
        with pytest.raises(ValueError):
            Config(
                bot_token="test_token",
                bot_username="testbot",
                super_admin_id=123456789,
                db_password="testpass",
                jwt_secret="a" * 32,
                log_level="INVALID"
            )
    
    def test_config_validation_log_level_uppercase(self) -> None:
        """Test that log level is converted to uppercase."""
        config = Config(
            bot_token="test_token",
            bot_username="testbot",
            super_admin_id=123456789,
            db_password="testpass",
            jwt_secret="a" * 32,
            log_level="info"
        )
        assert config.log_level == "INFO"
    
    def test_config_defaults(self) -> None:
        """Test that default values are set correctly."""
        config = Config(
            bot_token="test_token",
            bot_username="testbot",
            super_admin_id=123456789,
            db_password="testpass",
            jwt_secret="a" * 32
        )
        
        assert config.db_host == "localhost"
        assert config.db_port == 5432
        assert config.db_name == "swiftdevbot"
        assert config.db_user == "postgres"
        assert config.redis_host == "localhost"
        assert config.redis_port == 6379
        assert config.web_panel_url == "http://localhost:8000"
        assert config.log_level == "INFO"
    
    def test_config_db_url_postgresql(self) -> None:
        """Test PostgreSQL database URL generation."""
        config = Config(
            bot_token="test_token",
            bot_username="testbot",
            super_admin_id=123456789,
            db_type="postgresql",
            db_host="example.com",
            db_port=5433,
            db_name="testdb",
            db_user="testuser",
            db_password="testpass",
            jwt_secret="a" * 32
        )
        
        expected = "postgresql+asyncpg://testuser:testpass@example.com:5433/testdb"
        assert config.db_url == expected
    
    def test_config_db_url_sqlite(self) -> None:
        """Test SQLite database URL generation."""
        config = Config(
            bot_token="test_token",
            bot_username="testbot",
            super_admin_id=123456789,
            db_type="sqlite",
            db_path="test.db",
            jwt_secret="a" * 32
        )
        
        assert config.db_url.startswith("sqlite+aiosqlite:///")
        assert config.db_url.endswith("test.db")
    
    def test_config_db_url_memory(self) -> None:
        """Test in-memory SQLite database URL generation."""
        config = Config(
            bot_token="test_token",
            bot_username="testbot",
            super_admin_id=123456789,
            db_type="memory",
            jwt_secret="a" * 32
        )
        
        assert config.db_url == "sqlite+aiosqlite:///:memory:"
    
    def test_config_db_type_validation(self) -> None:
        """Test database type validation."""
        # Valid types
        for db_type in ["postgresql", "sqlite", "memory", "POSTGRESQL", "SQLite", "MEMORY"]:
            config = Config(
                bot_token="test_token",
                bot_username="testbot",
                super_admin_id=123456789,
                db_type=db_type,
                jwt_secret="a" * 32
            )
            assert config.db_type in {"postgresql", "sqlite", "memory"}
        
        # Invalid type
        with pytest.raises(ValueError, match="DB_TYPE must be one of"):
            Config(
                bot_token="test_token",
                bot_username="testbot",
                super_admin_id=123456789,
                db_type="mysql",
                jwt_secret="a" * 32
            )
    
    def test_config_redis_url(self) -> None:
        """Test Redis URL generation."""
        config = Config(
            bot_token="test_token",
            bot_username="testbot",
            super_admin_id=123456789,
            redis_host="redis.example.com",
            redis_port=6380,
            db_password="testpass",
            jwt_secret="a" * 32
        )
        
        expected = "redis://redis.example.com:6380"
        assert config.redis_url == expected
    
    def test_config_log_config_no_exception(self) -> None:
        """Test that log_config doesn't raise exceptions."""
        config = Config(
            bot_token="test_token",
            bot_username="testbot",
            super_admin_id=123456789,
            db_password="testpass",
            jwt_secret="a" * 32
        )
        
        # Should not raise any exception
        config.log_config()


class TestGetConfig:
    """Test cases for get_config function."""
    
    def test_get_config_initialization(self) -> None:
        """Test that get_config initializes config correctly."""
        with patch("Systems.core.utils.config.Config") as mock_config_class:
            mock_config = mock_config_class.return_value
            
            # Reset global config
            import Systems.core.utils.config as config_module
            config_module._config = None
            
            result = get_config()
            
            assert result == mock_config
            mock_config_class.assert_called_once()
    
    def test_get_config_cached(self) -> None:
        """Test that get_config returns cached config on second call."""
        with patch("Systems.core.utils.config.Config") as mock_config_class:
            mock_config = mock_config_class.return_value
            
            # Reset global config
            import Systems.core.utils.config as config_module
            config_module._config = None
            
            first = get_config()
            second = get_config()
            
            assert first == second
            assert first == mock_config
            # Should only be called once due to caching
            assert mock_config_class.call_count == 1


class TestReloadConfig:
    """Test cases for reload_config function."""
    
    def test_reload_config_force_reload(self) -> None:
        """Test that reload_config forces config reload."""
        with patch("Systems.core.utils.config.Config") as mock_config_class:
            # Create two different mock objects
            mock_config1 = MagicMock()
            mock_config2 = MagicMock()
            
            # Use side_effect to return different objects on each call
            mock_config_class.side_effect = [mock_config1, mock_config2]
            
            # Reset global config
            import Systems.core.utils.config as config_module
            config_module._config = None
            
            first = get_config()
            
            reloaded = reload_config()
            
            assert reloaded == mock_config2
            assert reloaded != first
            assert reloaded != mock_config1
            # Should be called twice (once for get_config, once for reload)
            assert mock_config_class.call_count == 2

