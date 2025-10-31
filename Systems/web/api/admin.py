"""
Admin API router.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from Systems.core.database import get_session_factory
from Systems.core.database.repositories.audit_repository import AuditRepository
from Systems.core.user.user_service import UserService
from Systems.web.api.schemas import AuditLogResponse, ErrorResponse, StatsResponse
from Systems.web.auth.dependencies import require_admin

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get(
    "/stats",
    response_model=StatsResponse,
    responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
)
async def get_stats(
    current_user: Any = Depends(require_admin),
) -> StatsResponse:
    """
    Get system statistics (admin only).
    
    Returns:
        System statistics
        
    Raises:
        HTTPException: 401 if not authenticated, 403 if not admin
        
    Example:
        ```python
        GET /api/admin/stats
        Authorization: Bearer <token>
        ```
    """
    session_factory = get_session_factory()
    
    async with session_factory() as session:
        user_service = UserService(session)
        
        # Get user statistics
        all_users = await user_service.list_users()
        active_users = [u for u in all_users if u.is_active]
        
        # Get module statistics
        from Systems.core.modules.manager import ModuleManager
        from Systems.core.modules.loader import ModuleLoader
        from pathlib import Path
        
        # Use default modules path
        modules_path = Path("Modules")
        
        total_modules = 0
        enabled_modules = 0
        total_commands = 0
        total_settings = 0
        
        if modules_path.exists():
            loader = ModuleLoader(modules_path)
            manager = ModuleManager(loader, db_session=session)
            
            modules = await manager.get_available_modules()
            total_modules = len(modules)
            enabled_modules = sum(1 for m in modules if m.enabled)
            
            for module in modules:
                total_commands += len(module.manifest.commands)
                total_settings += len(module.manifest.settings)
        
        return StatsResponse(
            total_users=len(all_users),
            active_users=len(active_users),
            total_modules=total_modules,
            enabled_modules=enabled_modules,
            total_commands=total_commands,
            total_settings=total_settings,
        )


@router.get(
    "/audit-logs",
    response_model=list[AuditLogResponse],
    responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
)
async def get_audit_logs(
    current_user: Any = Depends(require_admin),
    user_id: int | None = None,
    limit: int = 100,
    skip: int = 0,
) -> list[AuditLogResponse]:
    """
    Get audit logs (admin only).
    
    Args:
        current_user: Current user (admin required)
        user_id: Filter by user ID (optional)
        limit: Maximum number of logs to return
        skip: Number of logs to skip
        
    Returns:
        List of audit logs
        
    Raises:
        HTTPException: 401 if not authenticated, 403 if not admin
        
    Example:
        ```python
        GET /api/admin/audit-logs?limit=100&skip=0
        Authorization: Bearer <token>
        ```
    """
    session_factory = get_session_factory()
    
    async with session_factory() as session:
        audit_repo = AuditRepository(session)
        
        # Get audit logs
        if user_id:
            logs = await audit_repo.get_logs(user_id, limit=limit)
        else:
            # Get all logs (requires additional method)
            # For now, return empty list
            logs = []
        
        return [
            AuditLogResponse(
                id=log.id,
                user_id=log.user_id,
                action=log.action,
                resource=log.resource,
                old_value=log.old_value,
                new_value=log.new_value,
                ip_address=log.ip_address,
                success=log.success,
                timestamp=log.timestamp.isoformat() if log.timestamp else "",
            )
            for log in logs[skip : skip + limit]
        ]


@router.get(
    "/active-sessions",
    response_model=list[dict[str, Any]],
    responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
)
async def get_active_sessions(
    current_user: Any = Depends(require_admin),
) -> list[dict[str, Any]]:
    """
    Get active sessions (admin only).
    
    Returns:
        List of active sessions
        
    Raises:
        HTTPException: 401 if not authenticated, 403 if not admin
        
    Example:
        ```python
        GET /api/admin/active-sessions
        Authorization: Bearer <token>
        ```
    """
    # TODO: Implement session tracking
    # For now, return empty list
    return []

