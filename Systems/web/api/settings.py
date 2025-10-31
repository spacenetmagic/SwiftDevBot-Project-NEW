"""
Settings API router.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from Systems.core.database import get_session_factory
from Systems.core.database.repositories.settings_repository import SettingsRepository
from Systems.core.modules.manager import ModuleManager
from Systems.core.modules.loader import ModuleLoader
from Systems.web.api.schemas import ErrorResponse, SettingResponse, SettingUpdate
from Systems.web.auth.dependencies import get_current_user, require_admin

router = APIRouter(prefix="/api/settings", tags=["settings"])


def get_module_manager() -> ModuleManager:
    """Get module manager instance."""
    from pathlib import Path
    
    # Use default modules path
    modules_path = Path("Modules")
    
    loader = ModuleLoader(modules_path)
    manager = ModuleManager(loader, db_session=None)
    
    return manager


@router.get(
    "/{module_name}/user",
    response_model=dict[str, Any],
    responses={401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
async def get_user_settings(
    module_name: str,
    current_user: Any = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Get user settings for a module.
    
    Args:
        module_name: Module name
        current_user: Current user
        
    Returns:
        Dictionary of user settings
        
    Raises:
        HTTPException: 401 if not authenticated, 404 if module not found
        
    Example:
        ```python
        GET /api/settings/my_module/user
        Authorization: Bearer <token>
        ```
    """
    session_factory = get_session_factory()
    
    async with session_factory() as session:
        settings_repo = SettingsRepository(session)
        
        # Get all user settings for module
        # This requires additional method in repository
        # For now, return empty dict
        return {}


@router.put(
    "/{module_name}/user/{key}",
    response_model=SettingResponse,
    responses={401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
async def update_user_setting(
    module_name: str,
    key: str,
    setting_data: SettingUpdate,
    current_user: Any = Depends(get_current_user),
) -> SettingResponse:
    """
    Update user setting for a module.
    
    Args:
        module_name: Module name
        key: Setting key
        setting_data: Setting update data
        current_user: Current user
        
    Returns:
        Updated setting
        
    Raises:
        HTTPException: 401 if not authenticated, 404 if module not found
        
    Example:
        ```python
        PUT /api/settings/my_module/user/theme
        Authorization: Bearer <token>
        Content-Type: application/json
        
        {
            "value": "dark"
        }
        ```
    """
    session_factory = get_session_factory()
    
    async with session_factory() as session:
        settings_repo = SettingsRepository(session)
        
        # Get module manifest for validation
        manager = get_module_manager()
        module = manager.loader.get_loaded_module(module_name)
        
        if not module:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Module {module_name} not found",
            )
        
        # Update setting
        await settings_repo.set_user_setting(
            module_name, current_user.telegram_id, key, setting_data.value
        )
        await session.commit()
        
        # Get updated setting
        setting = await settings_repo.get_user_setting(
            module_name, current_user.telegram_id, key
        )
        
        if not setting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Setting {key} not found",
            )
        
        return SettingResponse(
            module_name=setting.module_name,
            key=setting.setting_key,
            value=setting.setting_value,
            level="user",
            user_id=setting.user_id,
        )


@router.get(
    "/{module_name}/admin",
    response_model=dict[str, Any],
    responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
async def get_admin_settings(
    module_name: str,
    current_user: Any = Depends(require_admin),
) -> dict[str, Any]:
    """
    Get admin settings for a module (admin only).
    
    Args:
        module_name: Module name
        current_user: Current user (admin required)
        
    Returns:
        Dictionary of admin settings
        
    Raises:
        HTTPException: 401 if not authenticated, 403 if not admin, 404 if module not found
        
    Example:
        ```python
        GET /api/settings/my_module/admin
        Authorization: Bearer <token>
        ```
    """
    session_factory = get_session_factory()
    
    async with session_factory() as session:
        settings_repo = SettingsRepository(session)
        
        # Get all admin settings for module
        # This requires additional method in repository
        # For now, return empty dict
        return {}


@router.put(
    "/{module_name}/admin/{key}",
    response_model=SettingResponse,
    responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
async def update_admin_setting(
    module_name: str,
    key: str,
    setting_data: SettingUpdate,
    current_user: Any = Depends(require_admin),
) -> SettingResponse:
    """
    Update admin setting for a module (admin only).
    
    Args:
        module_name: Module name
        key: Setting key
        setting_data: Setting update data
        current_user: Current user (admin required)
        
    Returns:
        Updated setting
        
    Raises:
        HTTPException: 401 if not authenticated, 403 if not admin, 404 if module not found
        
    Example:
        ```python
        PUT /api/settings/my_module/admin/max_users
        Authorization: Bearer <token>
        Content-Type: application/json
        
        {
            "value": 100
        }
        ```
    """
    session_factory = get_session_factory()
    
    async with session_factory() as session:
        settings_repo = SettingsRepository(session)
        
        # Get module manifest for validation
        manager = get_module_manager()
        module = manager.loader.get_loaded_module(module_name)
        
        if not module:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Module {module_name} not found",
            )
        
        # Update setting
        await settings_repo.set_admin_setting(module_name, key, setting_data.value)
        await session.commit()
        
        # Get updated setting
        setting = await settings_repo.get_admin_setting(module_name, key)
        
        if not setting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Setting {key} not found",
            )
        
        return SettingResponse(
            module_name=setting.module_name,
            key=setting.setting_key,
            value=setting.setting_value,
            level="admin",
            user_id=None,
        )


@router.get(
    "/{module_name}/schema",
    response_model=dict[str, Any],
    responses={401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
async def get_setting_schema(
    module_name: str,
    current_user: Any = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Get JSON schema for module settings (for UI).
    
    Args:
        module_name: Module name
        current_user: Current user
        
    Returns:
        JSON schema for settings
        
    Raises:
        HTTPException: 401 if not authenticated, 404 if module not found
        
    Example:
        ```python
        GET /api/settings/my_module/schema
        Authorization: Bearer <token>
        ```
    """
    manager = get_module_manager()
    module = manager.loader.get_loaded_module(module_name)
    
    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Module {module_name} not found",
        )
    
    # Return settings schema from manifest
    return module.manifest.settings

