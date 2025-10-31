"""
FastAPI routes for authentication.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from Systems.core.database import get_db
from Systems.core.database.models.user import User
from Systems.core.database.repositories.audit_repository import AuditRepository
from Systems.core.logger import get_logger
from Systems.web.auth.dependencies import get_current_user, get_jwt_handler
from Systems.web.auth.telegram_auth import TelegramAuth

logger = get_logger(__name__)

router = APIRouter(prefix="/api/auth", tags=["authentication"])

security = HTTPBearer()


# Request/Response models
class TelegramLoginRequest(BaseModel):
    """Telegram login request model."""
    
    id: int = Field(..., description="User Telegram ID")
    first_name: str = Field(..., description="User first name")
    username: str | None = Field(None, description="User username")
    last_name: str | None = Field(None, description="User last name")
    photo_url: str | None = Field(None, description="User photo URL")
    auth_date: int = Field(..., description="Authentication timestamp")
    hash: str = Field(..., description="Telegram hash")


class RefreshTokenRequest(BaseModel):
    """Refresh token request model."""
    
    refresh_token: str = Field(..., description="Refresh token")


class AuthResponse(BaseModel):
    """Authentication response model."""
    
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    user: dict[str, Any] = Field(..., description="User information")


class RefreshResponse(BaseModel):
    """Refresh token response model."""
    
    access_token: str = Field(..., description="New JWT access token")


class LogoutResponse(BaseModel):
    """Logout response model."""
    
    message: str = Field(default="Logged out successfully")


def user_to_dict(user: User) -> dict[str, Any]:
    """
    Convert User model to dictionary.
    
    Args:
        user: User object
        
    Returns:
        Dictionary with user data
    """
    return {
        "telegram_id": user.telegram_id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "photo_url": user.photo_url,
        "role": user.role.value,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


@router.post(
    "/telegram-login",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
)
async def telegram_login(
    request: TelegramLoginRequest,
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    """
    Authenticate user via Telegram login.
    
    Verifies Telegram auth data and creates JWT tokens.
    
    Args:
        request: Telegram login request
        db: Database session
        
    Returns:
        AuthResponse with tokens and user data
        
    Raises:
        HTTPException: If authentication fails
    """
    try:
        # Convert request to dict for TelegramAuth
        auth_data = request.model_dump()
        
        # Authenticate user
        telegram_auth = TelegramAuth(db)
        user = await telegram_auth.authenticate_user(auth_data)
        
        # Create JWT tokens
        jwt_handler = get_jwt_handler()
        access_token = await jwt_handler.create_access_token(
            user_id=user.telegram_id,
            username=user.username,
            role=user.role.value,
        )
        refresh_token = await jwt_handler.create_refresh_token(user.telegram_id)
        
        # Log authentication
        audit_repo = AuditRepository(db)
        await audit_repo.log(
            user_id=user.telegram_id,
            action="login",
            resource="web_panel",
            new_value={"method": "telegram"},
            success=True,
        )
        await db.commit()
        
        logger.info(f"User logged in successfully: {user.telegram_id} (@{user.username})")
        
        return AuthResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=user_to_dict(user),
        )
        
    except ValueError as e:
        logger.warning(f"Login failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"Unexpected login error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed",
        ) from e


@router.post(
    "/refresh",
    response_model=RefreshResponse,
    status_code=status.HTTP_200_OK,
)
async def refresh_token(
    request: RefreshTokenRequest,
) -> RefreshResponse:
    """
    Refresh access token using refresh token.
    
    Args:
        request: Refresh token request
        
    Returns:
        RefreshResponse with new access token
        
    Raises:
        HTTPException: If refresh token is invalid
    """
    try:
        jwt_handler = get_jwt_handler()
        new_access_token = await jwt_handler.refresh_access_token(request.refresh_token)
        
        logger.debug("Access token refreshed successfully")
        
        return RefreshResponse(access_token=new_access_token)
        
    except Exception as e:
        logger.warning(f"Token refresh failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        ) from e


@router.post(
    "/logout",
    response_model=LogoutResponse,
    status_code=status.HTTP_200_OK,
)
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LogoutResponse:
    """
    Logout user (invalidate session).
    
    Currently just logs the action. Token invalidation can be
    implemented via token blacklist in Redis.
    
    Args:
        credentials: HTTP Bearer credentials
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        LogoutResponse
    """
    try:
        # Log logout action
        audit_repo = AuditRepository(db)
        await audit_repo.log(
            user_id=current_user.telegram_id,
            action="logout",
            resource="web_panel",
            success=True,
        )
        await db.commit()
        
        logger.info(f"User logged out: {current_user.telegram_id}")
        
        return LogoutResponse(message="Logged out successfully")
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        # Still return success even if logging fails
        return LogoutResponse(message="Logged out successfully")

