"""
Audit log model for SwiftDevBot.
"""

from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from Systems.core.database import Base


class AuditLog(Base):
    """
    Audit log model for tracking user actions.
    
    Attributes:
        id: Primary key
        timestamp: Action timestamp
        user_id: User who performed the action (FK to User)
        action: Action name/type
        resource: Resource affected by the action
        old_value: Previous value (JSON, optional)
        new_value: New value (JSON, optional)
        ip_address: IP address of the user (optional)
        success: Whether the action was successful
    """
    
    __tablename__ = "audit_logs"
    
    # Primary key
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="Primary key",
    )
    
    # Timestamp
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Action timestamp",
    )
    
    # User reference
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.telegram_id", ondelete="SET NULL"),
        nullable=False,
        comment="User who performed the action",
    )
    
    # Action details
    action: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Action name/type",
    )
    
    resource: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Resource affected by the action",
    )
    
    # Values
    old_value: Mapped[Any | None] = mapped_column(
        JSON,
        nullable=True,
        comment="Previous value (JSON)",
    )
    
    new_value: Mapped[Any | None] = mapped_column(
        JSON,
        nullable=True,
        comment="New value (JSON)",
    )
    
    # Metadata
    ip_address: Mapped[str | None] = mapped_column(
        String(45),  # IPv6 max length
        nullable=True,
        comment="IP address of the user",
    )
    
    success: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Whether the action was successful",
    )
    
    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="audit_logs",
        foreign_keys=[user_id],
        lazy="selectin",
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_audit_logs_timestamp", "timestamp"),
        Index("idx_audit_logs_user_id", "user_id"),
        Index("idx_audit_logs_action", "action"),
        Index("idx_audit_logs_resource", "resource"),
        Index("idx_audit_logs_user_action", "user_id", "action"),
    )
    
    def __repr__(self) -> str:
        """String representation of AuditLog."""
        return (
            f"<AuditLog(id={self.id}, user_id={self.user_id}, "
            f"action={self.action}, resource={self.resource}, success={self.success})>"
        )

