"""
Module settings model for SwiftDevBot.
"""

import enum
from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, Index, Integer, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from Systems.core.database import Base


class SettingLevel(str, enum.Enum):
    """Setting level enumeration."""
    
    USER_SETTING = "user_setting"
    ADMIN_SETTING = "admin_setting"


class ModuleSetting(Base):
    """
    Module settings model for storing module-specific settings.
    
    Settings can be either user-specific (user_setting) or admin-wide (admin_setting).
    
    Attributes:
        id: Primary key
        module_name: Name of the module
        level: Setting level (user_setting or admin_setting)
        user_id: User ID for user settings (optional, FK to User)
        setting_key: Setting key name
        setting_value: Setting value (JSON)
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """
    
    __tablename__ = "module_settings"
    
    # Primary key
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="Primary key",
    )
    
    # Module info
    module_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Name of the module",
    )
    
    level: Mapped[SettingLevel] = mapped_column(
        Enum(SettingLevel, native_enum=False),
        nullable=False,
        comment="Setting level (user_setting or admin_setting)",
    )
    
    # User reference (only for user_setting level)
    user_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.telegram_id", ondelete="CASCADE"),
        nullable=True,
        comment="User ID for user settings",
    )
    
    # Setting key-value pair
    setting_key: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Setting key name",
    )
    
    setting_value: Mapped[Any] = mapped_column(
        JSON,
        nullable=False,
        comment="Setting value (JSON)",
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Creation timestamp",
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="Last update timestamp",
    )
    
    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        foreign_keys=[user_id],
        lazy="selectin",
    )
    
    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint(
            "module_name",
            "level",
            "user_id",
            "setting_key",
            name="uq_module_setting_key",
        ),
        Index("idx_module_settings_module_name", "module_name"),
        Index("idx_module_settings_level", "level"),
        Index("idx_module_settings_user_id", "user_id"),
        Index("idx_module_settings_module_user", "module_name", "user_id"),
    )
    
    def __repr__(self) -> str:
        """String representation of ModuleSetting."""
        return (
            f"<ModuleSetting(id={self.id}, module={self.module_name}, "
            f"level={self.level}, key={self.setting_key})>"
        )

