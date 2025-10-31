"""
Authentication package for SwiftDevBot web panel.
"""

from Systems.web.auth.dependencies import get_current_user, require_admin, require_super_admin
from Systems.web.auth.jwt_handler import JWTHandler
from Systems.web.auth.telegram_auth import TelegramAuth

__all__ = [
    "JWTHandler",
    "TelegramAuth",
    "get_current_user",
    "require_admin",
    "require_super_admin",
]

