"""
JWT token handler for authentication.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

from Systems.core.logger import get_logger
from Systems.core.utils.config import get_config


logger = get_logger(__name__)


class JWTHandler:
    """
    JWT token handler with RSA (RS256) signing.
    
    Manages access and refresh tokens for user authentication.
    """
    
    def __init__(self) -> None:
        """Initialize JWT handler and load/generate RSA keys."""
        self.config = get_config()
        self._private_key: bytes | None = None
        self._public_key: bytes | None = None
        
        # Token expiration times
        self.access_token_expire = timedelta(hours=24)
        self.refresh_token_expire = timedelta(days=7)
        
        self._load_or_generate_keys()
        logger.info("JWTHandler initialized")
    
    def _load_or_generate_keys(self) -> None:
        """
        Load RSA keys from files or generate new ones.
        
        Keys are stored in Data/security/ directory.
        """
        keys_dir = Path("Data/security")
        keys_dir.mkdir(parents=True, exist_ok=True)
        
        private_key_path = keys_dir / "jwt_private_key.pem"
        public_key_path = keys_dir / "jwt_public_key.pem"
        
        if private_key_path.exists() and public_key_path.exists():
            logger.info("Loading existing RSA keys")
            self._private_key = private_key_path.read_bytes()
            self._public_key = public_key_path.read_bytes()
        else:
            logger.info("Generating new RSA keys")
            self._generate_keys()
            private_key_path.write_bytes(self._private_key)
            public_key_path.write_bytes(self._public_key)
            logger.info(f"RSA keys saved to {keys_dir}")
    
    def _generate_keys(self) -> None:
        """Generate new RSA 2048-bit key pair."""
        private_key_obj = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        
        self._private_key = private_key_obj.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        
        public_key_obj = private_key_obj.public_key()
        self._public_key = public_key_obj.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        
        logger.debug("RSA 2048-bit keys generated successfully")
    
    async def create_access_token(
        self,
        user_id: int,
        username: str | None = None,
        role: str | None = None,
        expires_in: timedelta | None = None,
    ) -> str:
        """
        Create a JWT access token.
        
        Args:
            user_id: User Telegram ID
            username: User username (optional)
            role: User role (optional)
            expires_in: Token expiration time (default: 24 hours)
            
        Returns:
            Encoded JWT token string
        """
        if expires_in is None:
            expires_in = self.access_token_expire
        
        now = datetime.utcnow()
        payload = {
            "sub": str(user_id),  # Subject (user ID)
            "exp": now + expires_in,  # Expiration
            "iat": now,  # Issued at
            "type": "access",
            "username": username,
            "role": role,
        }
        
        token = jwt.encode(
            payload,
            self._private_key,
            algorithm="RS256",
        )
        
        logger.debug(f"Access token created for user {user_id}")
        return token
    
    async def create_refresh_token(self, user_id: int) -> str:
        """
        Create a JWT refresh token.
        
        Args:
            user_id: User Telegram ID
            
        Returns:
            Encoded JWT refresh token string
        """
        now = datetime.utcnow()
        payload = {
            "sub": str(user_id),
            "exp": now + self.refresh_token_expire,
            "iat": now,
            "type": "refresh",
        }
        
        token = jwt.encode(
            payload,
            self._private_key,
            algorithm="RS256",
        )
        
        logger.debug(f"Refresh token created for user {user_id}")
        return token
    
    async def verify_token(self, token: str) -> bool:
        """
        Verify if token is valid.
        
        Args:
            token: JWT token string
            
        Returns:
            True if token is valid, False otherwise
        """
        try:
            jwt.decode(
                token,
                self._public_key,
                algorithms=["RS256"],
            )
            return True
        except ExpiredSignatureError:
            logger.warning("Token verification failed: token expired")
            return False
        except InvalidTokenError as e:
            logger.warning(f"Token verification failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            return False
    
    async def decode_token(self, token: str) -> dict[str, Any]:
        """
        Decode and verify JWT token, returning claims.
        
        Args:
            token: JWT token string
            
        Returns:
            Dictionary with token claims
            
        Raises:
            ExpiredSignatureError: If token is expired
            InvalidTokenError: If token is invalid
        """
        try:
            payload = jwt.decode(
                token,
                self._public_key,
                algorithms=["RS256"],
            )
            logger.debug(f"Token decoded successfully for user {payload.get('sub')}")
            return payload
        except ExpiredSignatureError as e:
            logger.warning(f"Token expired: {e}")
            raise
        except InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            raise
        except Exception as e:
            logger.error(f"Token decode error: {e}")
            raise InvalidTokenError(f"Token decode failed: {e}") from e
    
    async def refresh_access_token(self, refresh_token: str) -> str:
        """
        Create a new access token from refresh token.
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            New access token
            
        Raises:
            InvalidTokenError: If refresh token is invalid or expired
        """
        try:
            payload = await self.decode_token(refresh_token)
            
            if payload.get("type") != "refresh":
                raise InvalidTokenError("Token is not a refresh token")
            
            user_id = int(payload.get("sub"))
            logger.info(f"Refreshing access token for user {user_id}")
            
            # Create new access token with user info if available
            new_token = await self.create_access_token(
                user_id=user_id,
            )
            
            return new_token
        except (ValueError, KeyError, TypeError) as e:
            logger.error(f"Refresh token processing error: {e}")
            raise InvalidTokenError(f"Invalid refresh token: {e}") from e
    
    def get_public_key(self) -> str:
        """
        Get public key as string for verification.
        
        Returns:
            Public key in PEM format
        """
        if self._public_key:
            return self._public_key.decode("utf-8")
        return ""

