"""
Configuration management module for SwiftDevBot.

This module provides configuration loading and validation using Pydantic settings.
All configuration values are loaded from environment variables via .env file.
"""

import logging
from pathlib import Path
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


logger = logging.getLogger(__name__)


class Config(BaseSettings):
    """
    Main configuration class for SwiftDevBot.
    
    Loads and validates all configuration values from environment variables.
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # Telegram Bot Configuration
    bot_token: str = Field(..., description="Telegram bot token")
    bot_username: str = Field(..., description="Telegram bot username")
    
    # Super Admin
    super_admin_id: int = Field(..., description="Super admin Telegram user ID")
    
    # Database Configuration
    db_type: str = Field(default="postgresql", description="Database type: postgresql, sqlite, or memory")
    db_host: str = Field(default="localhost", description="PostgreSQL host (ignored for SQLite)")
    db_port: int = Field(default=5432, description="PostgreSQL port (ignored for SQLite)")
    db_name: str = Field(default="swiftdevbot", description="Database name")
    db_user: str = Field(default="postgres", description="Database user (ignored for SQLite)")
    db_password: str = Field(default="", description="Database password (optional for SQLite)")
    db_path: str = Field(default="Data/database/swiftdevbot.db", description="SQLite database file path (for sqlite type)")
    
    # Redis Configuration (optional - will use MemoryStorage if disabled)
    use_redis: bool = Field(default=True, description="Enable Redis for FSM storage (disable to use MemoryStorage)")
    redis_host: str = Field(default="localhost", description="Redis host (ignored if use_redis=False)")
    redis_port: int = Field(default=6379, description="Redis port (ignored if use_redis=False)")
    
    # Web Panel Configuration
    web_panel_url: str = Field(default="http://localhost:8000", description="Web panel URL")
    
    # JWT Secret
    jwt_secret: str = Field(..., description="JWT secret key for authentication")
    
    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    
    @field_validator("bot_token")
    @classmethod
    def validate_bot_token(cls, v: str) -> str:
        """
        Validate bot token format.
        
        Args:
            v: Bot token value
            
        Returns:
            Validated bot token
            
        Raises:
            ValueError: If token is empty
        """
        if not v or not v.strip():
            raise ValueError("BOT_TOKEN cannot be empty")
        return v.strip()
    
    @field_validator("bot_username")
    @classmethod
    def validate_bot_username(cls, v: str) -> str:
        """
        Validate bot username format.
        
        Args:
            v: Bot username value
            
        Returns:
            Validated bot username
        """
        if v:
            # Remove @ if present
            return v.strip().lstrip("@")
        return v
    
    @field_validator("super_admin_id")
    @classmethod
    def validate_super_admin_id(cls, v: int) -> int:
        """
        Validate super admin ID.
        
        Args:
            v: Super admin ID value
            
        Returns:
            Validated super admin ID
            
        Raises:
            ValueError: If ID is not positive
        """
        if v <= 0:
            raise ValueError("SUPER_ADMIN_ID must be a positive integer")
        return v
    
    @field_validator("db_type")
    @classmethod
    def validate_db_type(cls, v: str) -> str:
        """
        Validate database type.
        
        Args:
            v: Database type value
            
        Returns:
            Validated database type (lowercase)
            
        Raises:
            ValueError: If type is invalid
        """
        valid_types = {"postgresql", "sqlite", "memory"}
        v_lower = v.lower()
        if v_lower not in valid_types:
            raise ValueError(f"DB_TYPE must be one of: {valid_types}")
        return v_lower
    
    @field_validator("db_port")
    @classmethod
    def validate_db_port(cls, v: int) -> int:
        """
        Validate database port.
        
        Args:
            v: Database port value
            
        Returns:
            Validated database port
            
        Raises:
            ValueError: If port is out of range
        """
        if not (1 <= v <= 65535):
            raise ValueError("DB_PORT must be between 1 and 65535")
        return v
    
    @field_validator("redis_port")
    @classmethod
    def validate_redis_port(cls, v: int) -> int:
        """
        Validate Redis port.
        
        Args:
            v: Redis port value
            
        Returns:
            Validated Redis port
            
        Raises:
            ValueError: If port is out of range
        """
        if not (1 <= v <= 65535):
            raise ValueError("REDIS_PORT must be between 1 and 65535")
        return v
    
    @field_validator("jwt_secret")
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        """
        Validate JWT secret length.
        
        Args:
            v: JWT secret value
            
        Returns:
            Validated JWT secret
            
        Raises:
            ValueError: If secret is less than 32 characters
        """
        if len(v) < 32:
            raise ValueError("JWT_SECRET must be at least 32 characters long")
        return v
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """
        Validate log level.
        
        Args:
            v: Log level value
            
        Returns:
            Validated log level (uppercase)
            
        Raises:
            ValueError: If log level is invalid
        """
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of: {valid_levels}")
        return v_upper
    
    @property
    def db_url(self) -> str:
        """
        Get database connection URL.
        
        Returns:
            Database connection URL (PostgreSQL, SQLite, or in-memory)
        """
        if self.db_type == "memory":
            return "sqlite+aiosqlite:///:memory:"
        elif self.db_type == "sqlite":
            from pathlib import Path
            db_path = Path(self.db_path)
            db_path.parent.mkdir(parents=True, exist_ok=True)
            return f"sqlite+aiosqlite:///{db_path.absolute()}"
        else:  # postgresql
            password_part = f":{self.db_password}" if self.db_password else ""
            return f"postgresql+asyncpg://{self.db_user}{password_part}@{self.db_host}:{self.db_port}/{self.db_name}"
    
    @property
    def redis_url(self) -> str:
        """
        Get Redis connection URL.
        
        Returns:
            Redis connection URL
        """
        return f"redis://{self.redis_host}:{self.redis_port}"
    
    def log_config(self) -> None:
        """
        Log configuration values (without sensitive data).
        """
        logger.info("=== SwiftDevBot Configuration ===")
        logger.info(f"Bot Username: {self.bot_username}")
        logger.info(f"Super Admin ID: {self.super_admin_id}")
        if self.db_type == "memory":
            logger.info(f"Database: SQLite (in-memory)")
        elif self.db_type == "sqlite":
            logger.info(f"Database: SQLite ({self.db_path})")
        else:
            logger.info(f"Database: PostgreSQL ({self.db_host}:{self.db_port}/{self.db_name})")
        if self.use_redis:
            logger.info(f"Redis: {self.redis_host}:{self.redis_port} (enabled)")
        else:
            logger.info("Redis: disabled (using MemoryStorage)")
        logger.info(f"Web Panel URL: {self.web_panel_url}")
        logger.info(f"Log Level: {self.log_level}")
        logger.info(f"Bot Token: {'*' * 10}...{self.bot_token[-4:] if len(self.bot_token) > 4 else '****'}")
        logger.info(f"JWT Secret: {'*' * 10}...{self.jwt_secret[-4:] if len(self.jwt_secret) > 4 else '****'}")
        logger.info("=================================")


# Global configuration instance
_config: Optional[Config] = None


def get_config() -> Config:
    """
    Get global configuration instance.
    
    Initializes configuration on first call if not already initialized.
    
    Returns:
        Configuration instance
        
    Raises:
        RuntimeError: If configuration validation fails
    """
    global _config
    
    if _config is None:
        try:
            logger.info("Loading configuration from environment...")
            _config = Config()
            _config.log_config()
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise RuntimeError(f"Configuration error: {e}") from e
    
    return _config


def reload_config() -> Config:
    """
    Reload configuration from environment.
    
    Returns:
        New configuration instance
        
    Raises:
        RuntimeError: If configuration validation fails
    """
    global _config
    
    logger.info("Reloading configuration from environment...")
    _config = None
    return get_config()

