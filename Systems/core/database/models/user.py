"""
User model for SwiftDevBot.
"""

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, DateTime, Enum, Index, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from Systems.core.database import Base

if TYPE_CHECKING:
    from Systems.core.database.models.audit_log import AuditLog


class UserRole(str, enum.Enum):
    """User role enumeration."""
    
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    MODERATOR = "moderator"
    USER = "user"


class User(Base):
    """
    User model representing a Telegram user.
    
    Attributes:
        telegram_id: Unique Telegram user ID (primary key)
        username: Telegram username (optional)
        first_name: User's first name
        last_name: User's last name (optional)
        photo_url: URL to user's profile photo (optional)
        role: User role (super_admin, admin, moderator, user)
        custom_permissions: Custom permissions JSON array
        is_active: Whether user is active
        created_at: Account creation timestamp
        updated_at: Last update timestamp
    """
    
    __tablename__ = "users"
    
    # Primary key
    telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        comment="Telegram user ID",
    )
    
    # Basic info
    username: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Telegram username",
    )
    
    first_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="User's first name",
    )
    
    last_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="User's last name",
    )
    
    photo_url: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
        comment="URL to user's profile photo",
    )
    
    # Role and permissions
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, native_enum=False),
        nullable=False,
        default=UserRole.USER,
        comment="User role",
    )
    
    custom_permissions: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        comment="Custom permissions JSON array",
    )
    
    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Whether user is active",
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Account creation timestamp",
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="Last update timestamp",
    )
    
    # Relationships
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_users_telegram_id", "telegram_id"),
        Index("idx_users_role", "role"),
        Index("idx_users_created_at", "created_at"),
        Index("idx_users_username", "username"),
    )
    
    def __repr__(self) -> str:
        """String representation of User."""
        return f"<User(telegram_id={self.telegram_id}, username={self.username}, role={self.role})>"

