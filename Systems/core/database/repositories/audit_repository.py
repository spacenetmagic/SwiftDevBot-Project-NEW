"""
Audit log repository for database operations.
"""

from typing import Any

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from Systems.core.database.models.audit_log import AuditLog
from Systems.core.logger import get_logger


logger = get_logger(__name__)


class AuditRepository:
    """
    Repository for AuditLog model operations.
    
    Provides methods for logging and querying audit logs.
    """
    
    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize repository with database session.
        
        Args:
            session: Async database session
        """
        self.session = session
        logger.debug("AuditRepository initialized")
    
    async def log(
        self,
        user_id: int,
        action: str,
        resource: str,
        old_value: Any | None = None,
        new_value: Any | None = None,
        ip_address: str | None = None,
        success: bool = True,
    ) -> AuditLog:
        """
        Create a new audit log entry.
        
        Args:
            user_id: User who performed the action
            action: Action name/type
            resource: Resource affected by the action
            old_value: Previous value (optional)
            new_value: New value (optional)
            ip_address: IP address of the user (optional)
            success: Whether the action was successful
            
        Returns:
            Created AuditLog instance
        """
        logger.debug(f"Creating audit log: user={user_id}, action={action}, resource={resource}")
        
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            resource=resource,
            old_value=old_value,
            new_value=new_value,
            ip_address=ip_address,
            success=success,
        )
        
        self.session.add(audit_log)
        await self.session.flush()
        await self.session.refresh(audit_log)
        
        logger.debug(f"Audit log created: id={audit_log.id}")
        return audit_log
    
    async def get_logs(
        self,
        user_id: int,
        limit: int = 100,
    ) -> list[AuditLog]:
        """
        Get audit logs for a specific user.
        
        Args:
            user_id: User ID to filter by
            limit: Maximum number of logs to return
            
        Returns:
            List of AuditLog instances, ordered by timestamp (newest first)
        """
        logger.debug(f"Fetching audit logs for user: {user_id}, limit={limit}")
        
        stmt = (
            select(AuditLog)
            .where(AuditLog.user_id == user_id)
            .order_by(desc(AuditLog.timestamp))
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        logs = result.scalars().all()
        
        logger.debug(f"Found {len(logs)} audit logs for user {user_id}")
        return list(logs)
    
    async def get_action_logs(
        self,
        action: str,
        limit: int = 100,
    ) -> list[AuditLog]:
        """
        Get audit logs for a specific action.
        
        Args:
            action: Action name to filter by
            limit: Maximum number of logs to return
            
        Returns:
            List of AuditLog instances, ordered by timestamp (newest first)
        """
        logger.debug(f"Fetching audit logs for action: {action}, limit={limit}")
        
        stmt = (
            select(AuditLog)
            .where(AuditLog.action == action)
            .order_by(desc(AuditLog.timestamp))
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        logs = result.scalars().all()
        
        logger.debug(f"Found {len(logs)} audit logs for action {action}")
        return list(logs)

