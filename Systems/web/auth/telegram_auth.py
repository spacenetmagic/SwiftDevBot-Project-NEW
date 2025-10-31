"""
Telegram authentication handler.
"""

import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from Systems.core.database.models.user import User, UserRole
from Systems.core.database.repositories.user_repository import UserRepository
from Systems.core.logger import get_logger
from Systems.core.utils.config import get_config


logger = get_logger(__name__)


class TelegramAuth:
    """
    Telegram authentication handler.
    
    Verifies Telegram login data and manages user authentication.
    """
    
    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize Telegram auth handler.
        
        Args:
            session: Database session
        """
        self.session = session
        self.config = get_config()
        self.user_repo = UserRepository(session)
        logger.debug("TelegramAuth initialized")
    
    def verify_telegram_auth(self, auth_data: dict[str, Any]) -> bool:
        """
        Verify Telegram authentication data.
        
        Checks:
        - Hash signature using bot token
        - Timestamp (not older than 24 hours)
        
        Args:
            auth_data: Dictionary with Telegram auth data:
                - id: User Telegram ID
                - first_name: User first name
                - username: User username (optional)
                - photo_url: User photo URL (optional)
                - auth_date: Unix timestamp
                - hash: HMAC SHA256 hash
                
        Returns:
            True if authentication is valid, False otherwise
        """
        try:
            # Check required fields
            required_fields = ["id", "auth_date", "hash"]
            for field in required_fields:
                if field not in auth_data:
                    logger.warning(f"Missing required field: {field}")
                    return False
            
            # Check timestamp (not older than 24 hours)
            auth_date = int(auth_data["auth_date"])
            auth_datetime = datetime.fromtimestamp(auth_date)
            now = datetime.utcnow()
            
            if (now - auth_datetime) > timedelta(hours=24):
                logger.warning(f"Auth data expired: {auth_date}")
                return False
            
            # Prepare data for hash verification
            data_check_string_parts = []
            
            # Sort keys and build check string (excluding hash)
            for key in sorted(auth_data.keys()):
                if key != "hash":
                    value = auth_data[key]
                    if isinstance(value, (list, dict)):
                        import json
                        value = json.dumps(value, separators=(",", ":"), ensure_ascii=False)
                    data_check_string_parts.append(f"{key}={value}")
            
            data_check_string = "\n".join(data_check_string_parts)
            
            # Calculate secret key
            secret_key = hmac.new(
                "WebAppData".encode("utf-8"),
                self.config.bot_token.encode("utf-8"),
                hashlib.sha256,
            ).digest()
            
            # Calculate hash
            calculated_hash = hmac.new(
                secret_key,
                data_check_string.encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()
            
            # Compare hashes
            received_hash = auth_data["hash"]
            
            if calculated_hash != received_hash:
                logger.warning("Hash verification failed")
                return False
            
            logger.debug("Telegram auth verification successful")
            return True
            
        except (ValueError, KeyError, TypeError) as e:
            logger.error(f"Telegram auth verification error: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error in Telegram auth: {e}")
            return False
    
    async def authenticate_user(self, auth_data: dict[str, Any]) -> User:
        """
        Authenticate user from Telegram data.
        
        Gets or creates user, updates profile from Telegram data.
        
        Args:
            auth_data: Verified Telegram auth data
            
        Returns:
            User object
            
        Raises:
            ValueError: If authentication data is invalid
        """
        # Verify auth data first
        if not self.verify_telegram_auth(auth_data):
            raise ValueError("Invalid Telegram authentication data")
        
        telegram_id = int(auth_data["id"])
        first_name = auth_data.get("first_name", "")
        username = auth_data.get("username")
        last_name = auth_data.get("last_name")
        photo_url = auth_data.get("photo_url")
        
        logger.info(f"Authenticating user: {telegram_id} (@{username})")
        
        # Try to get existing user
        user = await self.user_repo.get_by_id(telegram_id)
        
        if user:
            # Update user profile
            update_data = {
                "first_name": first_name,
                "username": username,
            }
            
            if last_name:
                update_data["last_name"] = last_name
            if photo_url:
                update_data["photo_url"] = photo_url
            
            user = await self.user_repo.update(telegram_id, update_data)
            await self.session.commit()
            
            logger.info(f"User profile updated: {telegram_id}")
        else:
            # Check if this is super admin
            config = get_config()
            role = UserRole.SUPER_ADMIN if telegram_id == config.super_admin_id else UserRole.USER
            
            # Create new user
            user_data = {
                "telegram_id": telegram_id,
                "username": username,
                "first_name": first_name,
                "last_name": last_name,
                "photo_url": photo_url,
                "role": role,
            }
            
            user = await self.user_repo.create(user_data)
            await self.session.commit()
            
            logger.info(f"New user created: {telegram_id} with role {role}")
        
        return user

