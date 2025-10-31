"""
Modules API router.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from Systems.core.database import get_session_factory
from Systems.core.modules.manager import ModuleManager
from Systems.core.modules.loader import ModuleLoader
from Systems.web.api.schemas import ErrorResponse, ModuleResponse
from Systems.web.auth.dependencies import get_current_user, require_admin

router = APIRouter(prefix="/api/modules", tags=["modules"])


def get_module_manager() -> ModuleManager:
    """Get module manager instance."""
    # This should be injected via dependency injection
    # For now, create on demand
    from pathlib import Path
    
    # Use default modules path
    modules_path = Path("Modules")
    
    if not modules_path:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Modules path not configured",
        )
    
    from pathlib import Path
    
    loader = ModuleLoader(Path(modules_path))
    manager = ModuleManager(loader, db_session=None)
    
    return manager


@router.get(
    "/",
    response_model=list[ModuleResponse],
    responses={401: {"model": ErrorResponse}},
)
async def list_modules(
    current_user: Any = Depends(get_current_user),
) -> list[ModuleResponse]:
    """
    List all available modules.
    
    Returns:
        List of modules
        
    Raises:
        HTTPException: 401 if not authenticated
        
    Example:
        ```python
        GET /api/modules/
        Authorization: Bearer <token>
        ```
    """
    manager = get_module_manager()
    modules = await manager.get_available_modules(current_user)
    
    return [
        ModuleResponse(
            name=module.name,
            display_name=module.manifest.display_name,
            version=module.manifest.version,
            description=module.manifest.description,
            author=module.manifest.author,
            enabled=module.enabled,
            enabled_by_default=module.manifest.enabled_by_default,
            dependencies=module.manifest.dependencies,
            commands=module.manifest.commands,
            settings=module.manifest.settings,
            languages=module.manifest.languages,
            background_tasks=module.manifest.background_tasks,
        )
        for module in modules
    ]


@router.get(
    "/{name}",
    response_model=ModuleResponse,
    responses={401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
async def get_module(
    name: str,
    current_user: Any = Depends(get_current_user),
) -> ModuleResponse:
    """
    Get module details.
    
    Args:
        name: Module name
        current_user: Current user
        
    Returns:
        Module details
        
    Raises:
        HTTPException: 401 if not authenticated, 404 if module not found
        
    Example:
        ```python
        GET /api/modules/my_module
        Authorization: Bearer <token>
        ```
    """
    manager = get_module_manager()
    module = manager.loader.get_loaded_module(name)
    
    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Module {name} not found",
        )
    
    return ModuleResponse(
        name=module.name,
        display_name=module.manifest.display_name,
        version=module.manifest.version,
        description=module.manifest.description,
        author=module.manifest.author,
        enabled=module.enabled,
        enabled_by_default=module.manifest.enabled_by_default,
        dependencies=module.manifest.dependencies,
        commands=module.manifest.commands,
        settings=module.manifest.settings,
        languages=module.manifest.languages,
        background_tasks=module.manifest.background_tasks,
    )


@router.post(
    "/{name}/enable",
    response_model=ModuleResponse,
    responses={401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
async def enable_module(
    name: str,
    current_user: Any = Depends(get_current_user),
) -> ModuleResponse:
    """
    Enable a module.
    
    Args:
        name: Module name
        current_user: Current user
        
    Returns:
        Enabled module
        
    Raises:
        HTTPException: 401 if not authenticated, 404 if module not found
        
    Example:
        ```python
        POST /api/modules/my_module/enable
        Authorization: Bearer <token>
        ```
    """
    manager = get_module_manager()
    
    try:
        module = await manager.enable_module(name)
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Module {name} not found",
        )
    
    return ModuleResponse(
        name=module.name,
        display_name=module.manifest.display_name,
        version=module.manifest.version,
        description=module.manifest.description,
        author=module.manifest.author,
        enabled=module.enabled,
        enabled_by_default=module.manifest.enabled_by_default,
        dependencies=module.manifest.dependencies,
        commands=module.manifest.commands,
        settings=module.manifest.settings,
        languages=module.manifest.languages,
        background_tasks=module.manifest.background_tasks,
    )


@router.post(
    "/{name}/disable",
    response_model=ModuleResponse,
    responses={401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
async def disable_module(
    name: str,
    current_user: Any = Depends(get_current_user),
) -> ModuleResponse:
    """
    Disable a module.
    
    Args:
        name: Module name
        current_user: Current user
        
    Returns:
        Disabled module
        
    Raises:
        HTTPException: 401 if not authenticated, 404 if module not found
        
    Example:
        ```python
        POST /api/modules/my_module/disable
        Authorization: Bearer <token>
        ```
    """
    manager = get_module_manager()
    
    module = manager.loader.get_loaded_module(name)
    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Module {name} not found",
        )
    
    await manager.disable_module(name)
    
    return ModuleResponse(
        name=module.name,
        display_name=module.manifest.display_name,
        version=module.manifest.version,
        description=module.manifest.description,
        author=module.manifest.author,
        enabled=module.enabled,
        enabled_by_default=module.manifest.enabled_by_default,
        dependencies=module.manifest.dependencies,
        commands=module.manifest.commands,
        settings=module.manifest.settings,
        languages=module.manifest.languages,
        background_tasks=module.manifest.background_tasks,
    )


@router.post(
    "/{name}/reload",
    response_model=ModuleResponse,
    responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
async def reload_module(
    name: str,
    current_user: Any = Depends(require_admin),
) -> ModuleResponse:
    """
    Reload a module (admin only).
    
    Args:
        name: Module name
        current_user: Current user (admin required)
        
    Returns:
        Reloaded module
        
    Raises:
        HTTPException: 401 if not authenticated, 403 if not admin, 404 if module not found
        
    Example:
        ```python
        POST /api/modules/my_module/reload
        Authorization: Bearer <token>
        ```
    """
    manager = get_module_manager()
    
    try:
        module = await manager.reload_module(name)
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Module {name} not found",
        )
    
    return ModuleResponse(
        name=module.name,
        display_name=module.manifest.display_name,
        version=module.manifest.version,
        description=module.manifest.description,
        author=module.manifest.author,
        enabled=module.enabled,
        enabled_by_default=module.manifest.enabled_by_default,
        dependencies=module.manifest.dependencies,
        commands=module.manifest.commands,
        settings=module.manifest.settings,
        languages=module.manifest.languages,
        background_tasks=module.manifest.background_tasks,
    )


@router.get(
    "/updates",
    response_model=list[ModuleResponse],
    responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
)
async def check_module_updates(
    current_user: Any = Depends(require_admin),
) -> list[ModuleResponse]:
    """
    Check for module updates (admin only).
    
    Returns:
        List of modules with available updates
        
    Raises:
        HTTPException: 401 if not authenticated, 403 if not admin
        
    Example:
        ```python
        GET /api/modules/updates
        Authorization: Bearer <token>
        ```
    """
    # TODO: Implement update checking logic
    # For now, return empty list
    return []

