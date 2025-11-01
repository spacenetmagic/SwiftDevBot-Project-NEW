"""
Users API router.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from Systems.core.database import get_session_factory
from Systems.core.database.models.user import User, UserRole
from Systems.core.user.user_service import UserService
from Systems.web.api.schemas import (
    ErrorResponse,
    RoleChange,
    UserCreate,
    UserResponse,
    UserUpdate,
)
from Systems.web.auth.dependencies import get_current_user, require_admin, require_super_admin

router = APIRouter(prefix="/api/users", tags=["users"])


def _normalize_text(value: str | None) -> str | None:
    """Trim string values and convert empty strings to None."""

    if value is None:
        return None

    cleaned = value.strip()
    return cleaned or None


def _split_full_name(full_name: str | None) -> tuple[str | None, str | None]:
    """Split full name into first and last name parts."""

    full_name = _normalize_text(full_name)
    if not full_name:
        return None, None

    parts = full_name.split(maxsplit=1)
    if not parts:
        return None, None

    first = parts[0]
    last = parts[1] if len(parts) > 1 else None
    return first, last


def _compose_full_name(first_name: str | None, last_name: str | None) -> str | None:
    """Compose full name from first and last name."""

    parts = [
        _normalize_text(first_name),
        _normalize_text(last_name),
    ]
    full_name = " ".join(part for part in parts if part)
    return full_name or None


def _user_to_response(user: User) -> UserResponse:
    """Convert a User ORM object to API response schema."""

    return UserResponse(
        telegram_id=user.telegram_id,
        username=_normalize_text(user.username),
        full_name=_compose_full_name(user.first_name, user.last_name),
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at.isoformat() if user.created_at else None,
        updated_at=user.updated_at.isoformat() if user.updated_at else None,
    )


@router.get("/me", response_model=UserResponse, responses={401: {"model": ErrorResponse}})
async def get_current_user_info(
    current_user: Any = Depends(get_current_user),
) -> UserResponse:
    """
    Get current user information.
    
    Returns:
        Current user information
        
    Raises:
        HTTPException: 401 if not authenticated
        
    Example:
        ```python
        GET /api/users/me
        Authorization: Bearer <token>
        ```
    """
    return _user_to_response(current_user)


@router.get(
    "/",
    response_model=list[UserResponse],
    responses={403: {"model": ErrorResponse}},
)
async def list_users(
    current_user: Any = Depends(require_admin),
    skip: int = 0,
    limit: int = 100,
) -> list[UserResponse]:
    """
    List all users (admin only).
    
    Args:
        current_user: Current user (admin required)
        skip: Number of users to skip
        limit: Maximum number of users to return
        
    Returns:
        List of users
        
    Raises:
        HTTPException: 403 if not admin
        
    Example:
        ```python
        GET /api/users/?skip=0&limit=100
        Authorization: Bearer <token>
        ```
    """
    session_factory = get_session_factory()
    
    async with session_factory() as session:
        user_service = UserService(session)
        users = await user_service.list_users(skip=skip, limit=limit)
        
        return [_user_to_response(user) for user in users]


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    responses={403: {"model": ErrorResponse}, 400: {"model": ErrorResponse}},
)
async def create_user(
    user_data: UserCreate,
    current_user: Any = Depends(require_admin),
) -> UserResponse:
    """
    Create a new user (admin only).
    
    Args:
        user_data: User creation data
        current_user: Current user (admin required)
        
    Returns:
        Created user
        
    Raises:
        HTTPException: 403 if not admin, 400 if user already exists
        
    Example:
        ```python
        POST /api/users/
        Authorization: Bearer <token>
        Content-Type: application/json

        {
            "telegram_id": 123456,
            "username": "testuser",
            "first_name": "Test",
            "last_name": "User",
            "role": "user"
        }
        ```
    """
    session_factory = get_session_factory()
    
    async with session_factory() as session:
        user_service = UserService(session)
        
        normalized_username = _normalize_text(user_data.username)
        first_name = _normalize_text(user_data.first_name)
        last_name = _normalize_text(user_data.last_name)

        derived_first, derived_last = _split_full_name(user_data.full_name)
        if not first_name and derived_first:
            first_name = derived_first
        if derived_last is not None and last_name is None:
            last_name = derived_last

        if not first_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="first_name or full_name must be provided",
            )

        try:
            user = await user_service.create_user(
                telegram_id=user_data.telegram_id,
                data={
                    "username": normalized_username,
                    "first_name": first_name,
                    "last_name": last_name,
                    "role": user_data.role,
                },
                created_by=current_user.telegram_id,
            )

            return _user_to_response(user)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            ) from e


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    responses={403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: Any = Depends(require_admin),
) -> UserResponse:
    """
    Update user (admin only).
    
    Args:
        user_id: User ID
        user_data: User update data
        current_user: Current user (admin required)
        
    Returns:
        Updated user
        
    Raises:
        HTTPException: 403 if not admin, 404 if user not found
        
    Example:
        ```python
        PUT /api/users/123456
        Authorization: Bearer <token>
        Content-Type: application/json
        
        {
            "username": "newusername",
            "is_active": true
        }
        ```
    """
    session_factory = get_session_factory()
    
    async with session_factory() as session:
        user_service = UserService(session)
        
        user = await user_service.get_user(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found",
            )
        
        # Update user
        if user_data.username is not None:
            user.username = user_data.username
        normalized_username = _normalize_text(user_data.username)
        normalized_first = _normalize_text(user_data.first_name)
        normalized_last = _normalize_text(user_data.last_name)

        split_first, split_last = _split_full_name(user_data.full_name)

        if normalized_username is not None:
            user.username = normalized_username
        if split_first and normalized_first is None:
            normalized_first = split_first
        if split_last is not None and normalized_last is None:
            normalized_last = _normalize_text(split_last)

        if normalized_first is not None:
            user.first_name = normalized_first
        if normalized_last is not None:
            user.last_name = normalized_last
        if user_data.is_active is not None:
            user.is_active = user_data.is_active

        await session.commit()
        await session.refresh(user)

        return _user_to_response(user)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
async def delete_user(
    user_id: int,
    current_user: Any = Depends(require_admin),
) -> None:
    """
    Delete user (admin only).
    
    Args:
        user_id: User ID
        current_user: Current user (admin required)
        
    Raises:
        HTTPException: 403 if not admin, 404 if user not found
        
    Example:
        ```python
        DELETE /api/users/123456
        Authorization: Bearer <token>
        ```
    """
    session_factory = get_session_factory()
    
    async with session_factory() as session:
        user_service = UserService(session)
        
        user = await user_service.get_user(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found",
            )
        
        await session.delete(user)
        await session.commit()


@router.put(
    "/{user_id}/role",
    response_model=UserResponse,
    responses={403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
async def change_user_role(
    user_id: int,
    role_data: RoleChange,
    current_user: Any = Depends(require_super_admin),
) -> UserResponse:
    """
    Change user role (super admin only).
    
    Args:
        user_id: User ID
        role_data: New role
        current_user: Current user (super admin required)
        
    Returns:
        Updated user
        
    Raises:
        HTTPException: 403 if not super admin, 404 if user not found
        
    Example:
        ```python
        PUT /api/users/123456/role
        Authorization: Bearer <token>
        Content-Type: application/json
        
        {
            "role": "admin"
        }
        ```
    """
    session_factory = get_session_factory()
    
    async with session_factory() as session:
        user_service = UserService(session)
        
        user = await user_service.get_user(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found",
            )
        
        await user_service.change_user_role(user_id, role_data.role)
        await session.commit()
        await session.refresh(user)
        
        return _user_to_response(user)

