"""
FastAPI dependencies for authentication and authorization.
"""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from Systems.core.database import get_db
from Systems.core.database.models.user import User, UserRole
from Systems.core.database.repositories.user_repository import UserRepository
from Systems.core.logger import get_logger
from Systems.web.auth.jwt_handler import JWTHandler

logger = get_logger(__name__)

# JWT handler instance (singleton)
_jwt_handler: JWTHandler | None = None


def get_jwt_handler() -> JWTHandler:
    """
    Get or create JWT handler instance.
    
    Returns:
        JWTHandler instance
    """
    global _jwt_handler
    
    if _jwt_handler is None:
        _jwt_handler = JWTHandler()
        logger.debug("JWT handler instance created")
    
    return _jwt_handler


# HTTP Bearer token scheme
security = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """
    Get current authenticated user from JWT token.
    
    Usage:
        @app.get("/protected")
        async def protected_route(user: User = Depends(get_current_user)):
            return {"user_id": user.telegram_id}
    
    Args:
        credentials: HTTP Bearer credentials
        db: Database session
        
    Returns:
        User object
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    token = credentials.credentials
    jwt_handler = get_jwt_handler()
    
    try:
        # Decode and verify token
        payload = await jwt_handler.decode_token(token)
        
        # Check token type
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )
        
        # Get user ID from token
        user_id = int(payload.get("sub"))
        
        # Get user from database
        user_repo = UserRepository(db)
        user = await user_repo.get_by_id(user_id)
        
        if not user:
            logger.warning(f"User not found: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )
        
        if not user.is_active:
            logger.warning(f"Inactive user attempted access: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive",
            )
        
        logger.debug(f"Authenticated user: {user_id}")
        return user
        
    except ValueError as e:
        logger.warning(f"Invalid token payload: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        ) from e
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
        ) from e


async def require_admin(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    Require admin or super_admin role.
    
    Usage:
        @app.get("/admin")
        async def admin_route(user: User = Depends(require_admin)):
            return {"message": "Admin only"}
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User object
        
    Raises:
        HTTPException: If user is not admin or super_admin
    """
    if current_user.role not in {UserRole.ADMIN, UserRole.SUPER_ADMIN}:
        logger.warning(f"Access denied for user {current_user.telegram_id}: requires admin role")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    
    return current_user


async def require_super_admin(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    Require super_admin role.
    
    Usage:
        @app.get("/super-admin")
        async def super_admin_route(user: User = Depends(require_super_admin)):
            return {"message": "Super admin only"}
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User object
        
    Raises:
        HTTPException: If user is not super_admin
    """
    if current_user.role != UserRole.SUPER_ADMIN:
        logger.warning(f"Access denied for user {current_user.telegram_id}: requires super_admin role")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin access required",
        )
    
    return current_user

