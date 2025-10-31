"""
Validation utilities for SwiftDevBot.

Provides validation functions for common data types and formats.
"""

from typing import Any


def validate_telegram_id(telegram_id: Any) -> int:
    """
    Validate Telegram user ID.
    
    Args:
        telegram_id: Telegram ID to validate (int or str)
        
    Returns:
        Valid Telegram ID as integer
        
    Raises:
        ValueError: If Telegram ID is invalid
        
    Examples:
        >>> validate_telegram_id(123456789)
        123456789
        >>> validate_telegram_id("123456789")
        123456789
        >>> validate_telegram_id(-1)
        Traceback (most recent call last):
        ...
        ValueError: Telegram ID must be positive
    """
    try:
        user_id = int(telegram_id)
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid Telegram ID: {telegram_id}") from e
    
    if user_id <= 0:
        raise ValueError("Telegram ID must be positive")
    
    # Telegram IDs are typically 9-10 digits
    if user_id > 999999999999:
        raise ValueError("Telegram ID too large")
    
    return user_id


def validate_username(username: str | None) -> str | None:
    """
    Validate Telegram username.
    
    Args:
        username: Username to validate (can be None)
        
    Returns:
        Valid username or None
        
    Raises:
        ValueError: If username format is invalid
        
    Examples:
        >>> validate_username("testuser")
        'testuser'
        >>> validate_username("test_user123")
        'test_user123'
        >>> validate_username("@testuser")
        'testuser'
        >>> validate_username("")
        Traceback (most recent call last):
        ...
        ValueError: Username cannot be empty
        >>> validate_username(None)
    """
    if username is None:
        return None
    
    username = username.strip()
    
    # Remove @ prefix if present
    if username.startswith("@"):
        username = username[1:]
    
    if not username:
        raise ValueError("Username cannot be empty")
    
    # Username validation: 5-32 characters, alphanumeric and underscores
    if len(username) < 5:
        raise ValueError("Username must be at least 5 characters")
    
    if len(username) > 32:
        raise ValueError("Username must be at most 32 characters")
    
    # Check characters: alphanumeric and underscores only
    if not username.replace("_", "").isalnum():
        raise ValueError("Username can only contain letters, numbers, and underscores")
    
    # Cannot start or end with underscore
    if username.startswith("_") or username.endswith("_"):
        raise ValueError("Username cannot start or end with underscore")
    
    return username


def validate_role(role: str | None) -> str:
    """
    Validate user role.
    
    Args:
        role: Role string to validate
        
    Returns:
        Valid role string
        
    Raises:
        ValueError: If role is invalid
        
    Examples:
        >>> validate_role("user")
        'user'
        >>> validate_role("admin")
        'admin'
        >>> validate_role("invalid")
        Traceback (most recent call last):
        ...
        ValueError: Invalid role: invalid
    """
    if not role:
        raise ValueError("Role cannot be empty")
    
    valid_roles = ["user", "admin", "super_admin", "moderator"]
    role_lower = role.lower().strip()
    
    if role_lower not in valid_roles:
        raise ValueError(f"Invalid role: {role}. Valid roles: {', '.join(valid_roles)}")
    
    return role_lower


def validate_module_name(module_name: str) -> str:
    """
    Validate module name.
    
    Args:
        module_name: Module name to validate
        
    Returns:
        Valid module name
        
    Raises:
        ValueError: If module name is invalid
        
    Examples:
        >>> validate_module_name("my_module")
        'my_module'
        >>> validate_module_name("My Module")
        Traceback (most recent call last):
        ...
        ValueError: Module name can only contain lowercase letters, numbers, and underscores
    """
    if not module_name:
        raise ValueError("Module name cannot be empty")
    
    module_name = module_name.strip()
    
    # Check length
    if len(module_name) < 2:
        raise ValueError("Module name must be at least 2 characters")
    
    if len(module_name) > 50:
        raise ValueError("Module name must be at most 50 characters")
    
    # Check characters: lowercase letters, numbers, underscores only
    if not module_name.replace("_", "").islower() and not module_name.replace("_", "").isalnum():
        raise ValueError("Module name can only contain lowercase letters, numbers, and underscores")
    
    # Cannot start or end with underscore
    if module_name.startswith("_") or module_name.endswith("_"):
        raise ValueError("Module name cannot start or end with underscore")
    
    return module_name


def validate_version(version: str) -> str:
    """
    Validate semantic version string.
    
    Args:
        version: Version string (e.g., "1.0.0")
        
    Returns:
        Valid version string
        
    Raises:
        ValueError: If version format is invalid
        
    Examples:
        >>> validate_version("1.0.0")
        '1.0.0'
        >>> validate_version("2.1.3")
        '2.1.3'
        >>> validate_version("invalid")
        Traceback (most recent call last):
        ...
        ValueError: Invalid version format: invalid
    """
    if not version:
        raise ValueError("Version cannot be empty")
    
    parts = version.split(".")
    
    if len(parts) != 3:
        raise ValueError(f"Invalid version format: {version}. Expected format: X.Y.Z")
    
    try:
        major = int(parts[0])
        minor = int(parts[1])
        patch = int(parts[2])
    except ValueError as e:
        raise ValueError(f"Invalid version format: {version}") from e
    
    if major < 0 or minor < 0 or patch < 0:
        raise ValueError("Version numbers must be non-negative")
    
    return version


def validate_setting_value(value: Any, setting_type: str, min_value: Any = None, max_value: Any = None) -> Any:
    """
    Validate setting value based on type and constraints.
    
    Args:
        value: Value to validate
        setting_type: Type of setting (string, integer, float, boolean)
        min_value: Minimum value (optional)
        max_value: Maximum value (optional)
        
    Returns:
        Validated value
        
    Raises:
        ValueError: If value is invalid
        
    Examples:
        >>> validate_setting_value("dark", "string")
        'dark'
        >>> validate_setting_value(100, "integer", min_value=1, max_value=1000)
        100
        >>> validate_setting_value(0, "integer", min_value=1)
        Traceback (most recent call last):
        ...
        ValueError: Value 0 is below minimum 1
    """
    if setting_type == "string":
        if not isinstance(value, str):
            raise ValueError(f"Setting expects string, got {type(value).__name__}")
        return value
    
    elif setting_type == "integer":
        try:
            int_value = int(value)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Setting expects integer, got {type(value).__name__}") from e
        
        if min_value is not None and int_value < min_value:
            raise ValueError(f"Value {int_value} is below minimum {min_value}")
        
        if max_value is not None and int_value > max_value:
            raise ValueError(f"Value {int_value} is above maximum {max_value}")
        
        return int_value
    
    elif setting_type == "float":
        try:
            float_value = float(value)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Setting expects float, got {type(value).__name__}") from e
        
        if min_value is not None and float_value < min_value:
            raise ValueError(f"Value {float_value} is below minimum {min_value}")
        
        if max_value is not None and float_value > max_value:
            raise ValueError(f"Value {float_value} is above maximum {max_value}")
        
        return float_value
    
    elif setting_type == "boolean":
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            lower = value.lower()
            if lower in ("true", "1", "yes", "on"):
                return True
            if lower in ("false", "0", "no", "off"):
                return False
        if isinstance(value, (int, float)):
            return bool(value)
        
        raise ValueError(f"Setting expects boolean, got {type(value).__name__}")
    
    else:
        raise ValueError(f"Unknown setting type: {setting_type}")


def validate_url(url: str) -> str:
    """
    Validate URL format.
    
    Args:
        url: URL string to validate
        
    Returns:
        Valid URL string
        
    Raises:
        ValueError: If URL format is invalid
        
    Examples:
        >>> validate_url("https://example.com")
        'https://example.com'
        >>> validate_url("invalid")
        Traceback (most recent call last):
        ...
        ValueError: Invalid URL format: invalid
    """
    if not url:
        raise ValueError("URL cannot be empty")
    
    url = url.strip()
    
    # Basic URL validation
    if not (url.startswith("http://") or url.startswith("https://")):
        raise ValueError(f"URL must start with http:// or https://: {url}")
    
    # Check for valid characters
    if " " in url:
        raise ValueError("URL cannot contain spaces")
    
    return url


def validate_email(email: str | None) -> str | None:
    """
    Validate email address format.
    
    Args:
        email: Email address to validate (can be None)
        
    Returns:
        Valid email address or None
        
    Raises:
        ValueError: If email format is invalid
        
    Examples:
        >>> validate_email("test@example.com")
        'test@example.com'
        >>> validate_email("invalid")
        Traceback (most recent call last):
        ...
        ValueError: Invalid email format: invalid
    """
    if email is None:
        return None
    
    email = email.strip()
    
    if not email:
        raise ValueError("Email cannot be empty")
    
    # Basic email validation
    if "@" not in email:
        raise ValueError(f"Invalid email format: {email}")
    
    parts = email.split("@")
    if len(parts) != 2:
        raise ValueError(f"Invalid email format: {email}")
    
    local, domain = parts
    
    if not local or not domain:
        raise ValueError(f"Invalid email format: {email}")
    
    if "." not in domain:
        raise ValueError(f"Invalid email domain: {domain}")
    
    return email

