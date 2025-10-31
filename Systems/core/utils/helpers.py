"""
Helper utilities for SwiftDevBot.

Provides general-purpose helper functions.
"""

import asyncio
import hashlib
import secrets
import string
from typing import Any, Callable, TypeVar
from functools import wraps

T = TypeVar("T")


def generate_random_string(length: int = 32, alphabet: str | None = None) -> str:
    """
    Generate random string.
    
    Args:
        length: Length of random string
        alphabet: Character alphabet (default: alphanumeric)
        
    Returns:
        Random string
        
    Examples:
        >>> len(generate_random_string(32))
        32
        >>> generate_random_string(8, alphabet="0123456789")
        '...'  # 8 digit string
    """
    if alphabet is None:
        alphabet = string.ascii_letters + string.digits
    
    return "".join(secrets.choice(alphabet) for _ in range(length))


def hash_string(value: str, algorithm: str = "sha256") -> str:
    """
    Hash string using specified algorithm.
    
    Args:
        value: String to hash
        algorithm: Hash algorithm (default: sha256)
        
    Returns:
        Hex hash string
        
    Examples:
        >>> hash_string("test")
        '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08'
        >>> hash_string("test", algorithm="md5")
        '098f6bcd4621d373cade4e832627b4f6'
    """
    hash_obj = hashlib.new(algorithm)
    hash_obj.update(value.encode("utf-8"))
    return hash_obj.hexdigest()


def safe_int(value: Any, default: int = 0) -> int:
    """
    Safely convert value to integer.
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
        
    Returns:
        Integer value or default
        
    Examples:
        >>> safe_int("123")
        123
        >>> safe_int("invalid", default=0)
        0
        >>> safe_int(None, default=-1)
        -1
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_float(value: Any, default: float = 0.0) -> float:
    """
    Safely convert value to float.
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
        
    Returns:
        Float value or default
        
    Examples:
        >>> safe_float("123.45")
        123.45
        >>> safe_float("invalid", default=0.0)
        0.0
    """
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_str(value: Any, default: str = "") -> str:
    """
    Safely convert value to string.
    
    Args:
        value: Value to convert
        default: Default value if None
        
    Returns:
        String value or default
        
    Examples:
        >>> safe_str(123)
        '123'
        >>> safe_str(None, default="default")
        'default'
    """
    if value is None:
        return default
    return str(value)


def chunk_list(lst: list[T], chunk_size: int) -> list[list[T]]:
    """
    Split list into chunks of specified size.
    
    Args:
        lst: List to chunk
        chunk_size: Size of each chunk
        
    Returns:
        List of chunks
        
    Examples:
        >>> chunk_list([1, 2, 3, 4, 5], 2)
        [[1, 2], [3, 4], [5]]
        >>> chunk_list([1, 2, 3], 1)
        [[1], [2], [3]]
    """
    if chunk_size <= 0:
        raise ValueError("Chunk size must be positive")
    
    return [lst[i : i + chunk_size] for i in range(0, len(lst), chunk_size)]


def retry_async(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator for retrying async functions.
    
    Args:
        max_attempts: Maximum number of attempts
        delay: Initial delay between attempts (seconds)
        backoff: Backoff multiplier
        exceptions: Exception types to catch
        
    Returns:
        Decorated function
        
    Examples:
        >>> @retry_async(max_attempts=3, delay=1.0)
        ... async def my_function():
        ...     # Will retry up to 3 times on exception
        ...     pass
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            current_delay = delay
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts:
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        raise
            
            if last_exception:
                raise last_exception
        
        return wrapper
    return decorator


def retry_sync(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator for retrying sync functions.
    
    Args:
        max_attempts: Maximum number of attempts
        delay: Initial delay between attempts (seconds)
        backoff: Backoff multiplier
        exceptions: Exception types to catch
        
    Returns:
        Decorated function
        
    Examples:
        >>> @retry_sync(max_attempts=3)
        ... def my_function():
        ...     # Will retry up to 3 times on exception
        ...     pass
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            import time
            current_delay = delay
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts:
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        raise
            
            if last_exception:
                raise last_exception
        
        return wrapper
    return decorator


def truncate_string(value: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate string to maximum length.
    
    Args:
        value: String to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated string
        
    Examples:
        >>> truncate_string("Hello World", 5)
        'He...'
        >>> truncate_string("Short", 10)
        'Short'
    """
    if len(value) <= max_length:
        return value
    
    if len(suffix) >= max_length:
        return value[:max_length]
    
    return value[: max_length - len(suffix)] + suffix


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing invalid characters.
    
    Args:
        filename: Filename to sanitize
        
    Returns:
        Sanitized filename
        
    Examples:
        >>> sanitize_filename("test/file.txt")
        'test_file.txt'
        >>> sanitize_filename("  invalid  .txt  ")
        'invalid.txt'
    """
    # Remove invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, "_")
    
    # Remove leading/trailing spaces and dots
    filename = filename.strip(" .")
    
    # Replace multiple spaces/underscores with single
    while "  " in filename:
        filename = filename.replace("  ", " ")
    while "__" in filename:
        filename = filename.replace("__", "_")
    
    return filename


def merge_dicts(*dicts: dict[str, Any]) -> dict[str, Any]:
    """
    Merge multiple dictionaries, later ones override earlier ones.
    
    Args:
        *dicts: Dictionaries to merge
        
    Returns:
        Merged dictionary
        
    Examples:
        >>> merge_dicts({"a": 1}, {"b": 2}, {"a": 3})
        {'a': 3, 'b': 2}
    """
    result: dict[str, Any] = {}
    for d in dicts:
        result.update(d)
    return result


def get_nested_value(data: dict[str, Any], path: str, default: Any = None) -> Any:
    """
    Get nested value from dictionary using dot notation.
    
    Args:
        data: Dictionary to search
        path: Dot-separated path (e.g., "user.settings.theme")
        default: Default value if path not found
        
    Returns:
        Value at path or default
        
    Examples:
        >>> data = {"user": {"settings": {"theme": "dark"}}}
        >>> get_nested_value(data, "user.settings.theme")
        'dark'
        >>> get_nested_value(data, "user.invalid", default="default")
        'default'
    """
    keys = path.split(".")
    value = data
    
    for key in keys:
        if isinstance(value, dict):
            value = value.get(key)
            if value is None:
                return default
        else:
            return default
    
    return value if value is not None else default


def set_nested_value(data: dict[str, Any], path: str, value: Any) -> None:
    """
    Set nested value in dictionary using dot notation.
    
    Args:
        data: Dictionary to modify
        path: Dot-separated path (e.g., "user.settings.theme")
        value: Value to set
        
    Examples:
        >>> data = {}
        >>> set_nested_value(data, "user.settings.theme", "dark")
        >>> data
        {'user': {'settings': {'theme': 'dark'}}}
    """
    keys = path.split(".")
    current = data
    
    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]
    
    current[keys[-1]] = value

