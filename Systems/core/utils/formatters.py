"""
Formatting utilities for SwiftDevBot.

Provides formatting functions for dates, times, numbers, and other data.
"""

from datetime import datetime, timedelta
from typing import Any


def format_datetime(dt: datetime | None, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format datetime to string.
    
    Args:
        dt: Datetime object to format
        format_str: Format string (default: "%Y-%m-%d %H:%M:%S")
        
    Returns:
        Formatted datetime string or empty string if None
        
    Examples:
        >>> from datetime import datetime
        >>> dt = datetime(2024, 1, 1, 12, 30, 45)
        >>> format_datetime(dt)
        '2024-01-01 12:30:45'
        >>> format_datetime(dt, "%Y-%m-%d")
        '2024-01-01'
        >>> format_datetime(None)
        ''
    """
    if dt is None:
        return ""
    
    return dt.strftime(format_str)


def format_date(dt: datetime | None) -> str:
    """
    Format datetime to date string.
    
    Args:
        dt: Datetime object to format
        
    Returns:
        Formatted date string (YYYY-MM-DD) or empty string if None
        
    Examples:
        >>> from datetime import datetime
        >>> dt = datetime(2024, 1, 1, 12, 30, 45)
        >>> format_date(dt)
        '2024-01-01'
    """
    return format_datetime(dt, "%Y-%m-%d")


def format_time(dt: datetime | None) -> str:
    """
    Format datetime to time string.
    
    Args:
        dt: Datetime object to format
        
    Returns:
        Formatted time string (HH:MM:SS) or empty string if None
        
    Examples:
        >>> from datetime import datetime
        >>> dt = datetime(2024, 1, 1, 12, 30, 45)
        >>> format_time(dt)
        '12:30:45'
    """
    return format_datetime(dt, "%H:%M:%S")


def format_timedelta(td: timedelta | None) -> str:
    """
    Format timedelta to human-readable string.
    
    Args:
        td: Timedelta object to format
        
    Returns:
        Human-readable timedelta string or empty string if None
        
    Examples:
        >>> from datetime import timedelta
        >>> format_timedelta(timedelta(days=1, hours=2, minutes=30))
        '1 day, 2 hours, 30 minutes'
        >>> format_timedelta(timedelta(seconds=90))
        '1 minute, 30 seconds'
    """
    if td is None:
        return ""
    
    total_seconds = int(td.total_seconds())
    
    if total_seconds < 60:
        return f"{total_seconds} second{'s' if total_seconds != 1 else ''}"
    
    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    
    parts = []
    
    if days > 0:
        parts.append(f"{days} day{'s' if days != 1 else ''}")
    if hours > 0:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if minutes > 0:
        parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
    if seconds > 0 and days == 0 and hours == 0:
        parts.append(f"{seconds} second{'s' if seconds != 1 else ''}")
    
    return ", ".join(parts) if parts else "0 seconds"


def format_number(number: int | float | None, precision: int = 2) -> str:
    """
    Format number with thousand separators.
    
    Args:
        number: Number to format
        precision: Decimal precision for floats (default: 2)
        
    Returns:
        Formatted number string or empty string if None
        
    Examples:
        >>> format_number(1234567)
        '1,234,567'
        >>> format_number(1234.567, precision=2)
        '1,234.57'
        >>> format_number(None)
        ''
    """
    if number is None:
        return ""
    
    if isinstance(number, float):
        formatted = f"{number:,.{precision}f}"
    else:
        formatted = f"{number:,}"
    
    return formatted


def format_bytes(bytes_count: int | None) -> str:
    """
    Format bytes to human-readable size.
    
    Args:
        bytes_count: Number of bytes
        
    Returns:
        Human-readable size string (e.g., "1.5 MB") or empty string if None
        
    Examples:
        >>> format_bytes(1024)
        '1.0 KB'
        >>> format_bytes(1048576)
        '1.0 MB'
        >>> format_bytes(1536)
        '1.5 KB'
    """
    if bytes_count is None:
        return ""
    
    if bytes_count == 0:
        return "0 B"
    
    units = ["B", "KB", "MB", "GB", "TB"]
    unit_index = 0
    size = float(bytes_count)
    
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    
    return f"{size:.1f} {units[unit_index]}"


def format_percentage(value: float | int, total: float | int | None = None, precision: int = 1) -> str:
    """
    Format value as percentage.
    
    Args:
        value: Value to format
        total: Total value for percentage calculation (optional)
        precision: Decimal precision (default: 1)
        
    Returns:
        Formatted percentage string
        
    Examples:
        >>> format_percentage(0.75)
        '75.0%'
        >>> format_percentage(3, total=10)
        '30.0%'
        >>> format_percentage(50, total=100, precision=0)
        '50%'
    """
    if total is not None and total != 0:
        percentage = (value / total) * 100
    else:
        percentage = value * 100
    
    return f"{percentage:.{precision}f}%"


def format_relative_time(dt: datetime | None) -> str:
    """
    Format datetime as relative time (e.g., "2 hours ago", "in 3 days").
    
    Args:
        dt: Datetime object to format
        
    Returns:
        Relative time string or empty string if None
        
    Examples:
        >>> from datetime import datetime, timedelta
        >>> now = datetime.now()
        >>> format_relative_time(now - timedelta(hours=2))
        '2 hours ago'
        >>> format_relative_time(now + timedelta(days=1))
        'in 1 day'
    """
    if dt is None:
        return ""
    
    now = datetime.now()
    diff = now - dt
    
    if abs(diff.total_seconds()) < 60:
        return "just now"
    
    if diff.total_seconds() > 0:
        # Past time
        return f"{format_timedelta(diff)} ago"
    else:
        # Future time
        return f"in {format_timedelta(-diff)}"


def format_username(username: str | None, telegram_id: int | None = None) -> str:
    """
    Format username with optional Telegram ID.
    
    Args:
        username: Username (can be None)
        telegram_id: Telegram ID (optional)
        
    Returns:
        Formatted username string
        
    Examples:
        >>> format_username("testuser")
        '@testuser'
        >>> format_username(None, telegram_id=123456789)
        '123456789'
        >>> format_username("testuser", telegram_id=123456789)
        '@testuser (123456789)'
    """
    if username:
        formatted = f"@{username}"
        if telegram_id:
            formatted += f" ({telegram_id})"
        return formatted
    
    if telegram_id:
        return str(telegram_id)
    
    return "Unknown"


def format_role(role: str | None) -> str:
    """
    Format user role for display.
    
    Args:
        role: Role string
        
    Returns:
        Formatted role string
        
    Examples:
        >>> format_role("super_admin")
        'Super Admin'
        >>> format_role("user")
        'User'
    """
    if not role:
        return "Unknown"
    
    return role.replace("_", " ").title()

