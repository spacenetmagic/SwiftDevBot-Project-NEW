"""
Logging configuration module for SwiftDevBot.

This module sets up logging for the entire application with file and console output.
Logs are written to Data/logs/ directory with rotation support.
Uses grouped logging by category (bot, web, db, modules) instead of per-module files.
Console logs use Rich for beautiful formatting, file logs use simple format.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

from logging.handlers import RotatingFileHandler

try:
    from rich.logging import RichHandler
    from rich.console import Console as RichConsole
    from rich import traceback
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

# Track if root logger is initialized
_root_logger_initialized = False


# Removed _get_log_category - no longer needed, filtering done in handlers


def _setup_root_logger(log_level: str = "INFO", log_dir: Optional[Path] = None) -> None:
    """
    Set up root logger with category-based file handlers.
    
    Creates separate log files for:
    - bot.log / bot_errors.log - Bot related logs
    - web.log / web_errors.log - Web panel logs
    - core.log / core_errors.log - Core system logs
    - modules.log / modules_errors.log - Module logs
    - app.log / app_errors.log - Everything else (fallback)
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files (default: Data/logs/)
    """
    global _root_logger_initialized
    
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    root_logger = logging.getLogger()
    
    if _root_logger_initialized:
        # Logger already initialized, just update handler levels
        for handler in root_logger.handlers:
            # Skip error-only handlers (they should stay at ERROR level)
            if hasattr(handler, 'level') and handler.level > logging.ERROR:
                continue
            
            # Update level for console handlers and file handlers (except error-only)
            if isinstance(handler, logging.StreamHandler):
                handler.setLevel(numeric_level)
            elif RICH_AVAILABLE and isinstance(handler, RichHandler):
                handler.setLevel(numeric_level)
            elif isinstance(handler, RotatingFileHandler):
                # Update file handler level (but keep error handlers at ERROR)
                if handler.level <= logging.ERROR:
                    handler.setLevel(numeric_level)
        
        # Update SQLAlchemy and aiogram logger levels
        _configure_external_loggers(log_level)
        return
    
    # Determine log directory
    if log_dir is None:
        log_dir = Path("Data/logs")
    else:
        log_dir = Path(log_dir)
    
    # Create log directory if it doesn't exist
    log_dir.mkdir(parents=True, exist_ok=True)
    
    root_logger.setLevel(logging.DEBUG)  # Set to lowest level, handlers will filter
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler with Rich formatting (beautiful, colorful output)
    if RICH_AVAILABLE:
        # Use Rich handler for beautiful console output
        console_handler = RichHandler(
            console=RichConsole(stderr=False, force_terminal=True),
            show_time=True,
            show_path=False,  # Don't show file path to keep logs clean
            rich_tracebacks=True,
            tracebacks_show_locals=False,
            markup=True,
            log_time_format="[%X]",  # HH:MM:SS format
        )
        console_handler.setLevel(numeric_level)
        # Rich handler has its own formatting, no need for formatter
        root_logger.addHandler(console_handler)
        
        # Enable rich traceback formatting
        traceback.install()
    else:
        # Fallback to simple console handler if Rich is not available
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        # Simple format for console if Rich not available
        simple_formatter = logging.Formatter(
            fmt="[%(asctime)s] %(levelname)-8s | %(message)s",
            datefmt="%H:%M:%S"
        )
        console_handler.setFormatter(simple_formatter)
        root_logger.addHandler(console_handler)
    
    # File formatter (simple, structured format for files)
    file_formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Category-based log files (order matters - more specific first)
    # bot must come before core, as bot starts with Systems.core.bot
    categories = {
        "bot": ["Systems.core.bot", "Systems.cli.commands.bot"],
        "web": ["Systems.web"],
        "modules": ["module.", "Modules."],
        "core": ["Systems.core", "Systems.cli"],  # Must be last as it matches Systems.core.*
    }
    
    # Create handlers for each category
    category_handlers = {}
    
    for category, prefixes in categories.items():
        # Create filter function with proper closure
        def make_category_filter(cat: str, prefs: list[str]):
            return lambda record: _should_log_to_category(record, cat, prefs)
        
        category_filter = make_category_filter(category, prefixes)
        
        # Regular log file for category
        category_log_file = log_dir / f"{category}.log"
        category_handler = RotatingFileHandler(
            category_log_file,
            maxBytes=50 * 1024 * 1024,  # 50 MB
            backupCount=5,
            encoding="utf-8"
        )
        category_handler.setLevel(numeric_level)
        category_handler.setFormatter(file_formatter)
        category_handler.addFilter(category_filter)
        root_logger.addHandler(category_handler)
        
        # Error log file for category
        category_error_file = log_dir / f"{category}_errors.log"
        category_error_handler = RotatingFileHandler(
            category_error_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding="utf-8"
        )
        category_error_handler.setLevel(logging.ERROR)
        category_error_handler.setFormatter(file_formatter)
        category_error_handler.addFilter(category_filter)
        root_logger.addHandler(category_error_handler)
        
        category_handlers[category] = (category_handler, category_error_handler)
    
    # Fallback app.log for everything else
    app_log_file = log_dir / "app.log"
    app_file_handler = RotatingFileHandler(
        app_log_file,
        maxBytes=50 * 1024 * 1024,  # 50 MB
        backupCount=5,
        encoding="utf-8"
    )
    app_file_handler.setLevel(numeric_level)
    app_file_handler.setFormatter(file_formatter)
    app_file_handler.addFilter(lambda record: not _matches_any_category(record, categories))
    root_logger.addHandler(app_file_handler)
    
    # Fallback error log
    app_error_file = log_dir / "app_errors.log"
    app_error_handler = RotatingFileHandler(
        app_error_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8"
    )
    app_error_handler.setLevel(logging.ERROR)
    app_error_handler.setFormatter(file_formatter)
    app_error_handler.addFilter(lambda record: not _matches_any_category(record, categories))
    root_logger.addHandler(app_error_handler)
    
    # Configure external library loggers
    _configure_external_loggers(log_level)
    
    _root_logger_initialized = True
    # Logger is ready, no need to log initialization (keep console clean)


def _configure_external_loggers(log_level: str) -> None:
    """
    Configure external library loggers to suppress verbose logs.
    
    Args:
        log_level: Current log level
    """
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Configure SQLAlchemy loggers to suppress verbose DEBUG logs
    # SQLAlchemy DEBUG logs are too verbose for normal operation (shows every SQL query)
    sqlalchemy_loggers = [
        "sqlalchemy.engine",
        "sqlalchemy.pool",
        "sqlalchemy.dialects",
        "sqlalchemy.orm",
        "sqlalchemy.events",
    ]
    
    for logger_name in sqlalchemy_loggers:
        sqlalchemy_logger = logging.getLogger(logger_name)
        sqlalchemy_logger.setLevel(logging.WARNING)  # Only show warnings and errors
        sqlalchemy_logger.propagate = True  # Propagate to root logger
    
    # Configure aiogram loggers - keep INFO for important messages
    aiogram_loggers = [
        "aiogram.dispatcher",
        "aiogram.client",
        "aiogram.webhook",
    ]
    
    for logger_name in aiogram_loggers:
        aiogram_logger = logging.getLogger(logger_name)
        # Keep INFO for important messages, suppress DEBUG unless explicitly requested
        if numeric_level <= logging.DEBUG:
            aiogram_logger.setLevel(logging.DEBUG)
        else:
            aiogram_logger.setLevel(logging.INFO)
        aiogram_logger.propagate = True
    
    # Suppress aiosqlite verbose logs (SQLite connection logs)
    aiosqlite_logger = logging.getLogger("aiosqlite")
    aiosqlite_logger.setLevel(logging.WARNING)
    aiosqlite_logger.propagate = True


def _should_log_to_category(record: logging.LogRecord, category: str, prefixes: list[str]) -> bool:
    """
    Check if log record should go to category log file.
    
    Args:
        record: Log record
        category: Category name (used for debugging)
        prefixes: List of prefixes to match against logger name
        
    Returns:
        True if record should be logged to this category
    """
    logger_name = record.name
    
    # Check if logger name starts with any prefix for this category
    for prefix in prefixes:
        if logger_name.startswith(prefix):
            return True
    
    return False


def _matches_any_category(record: logging.LogRecord, categories: dict[str, list[str]]) -> bool:
    """Check if log record matches any category."""
    logger_name = record.name
    
    for prefixes in categories.values():
        for prefix in prefixes:
            if logger_name.startswith(prefix):
                return True
    
    return False


def setup_logger(
    log_level: str = "INFO",
    log_dir: Optional[Path] = None,
    module_name: Optional[str] = None
) -> logging.Logger:
    """
    Set up root logger (for backward compatibility).
    
    This function can be called multiple times to update log level.
    If logger is already initialized, it will update handler levels.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files (default: Data/logs/)
        module_name: Ignored (kept for backward compatibility)
        
    Returns:
        Root logger instance
    """
    _setup_root_logger(log_level=log_level, log_dir=log_dir)
    return logging.getLogger(module_name if module_name else "swiftdevbot")


def get_logger(name: str, log_level: Optional[str] = None) -> logging.Logger:
    """
    Get or create a logger for a specific module.
    
    Logs are automatically routed to category files based on module name:
    - bot.log / bot_errors.log - Bot related (Systems.core.bot, Systems.cli.commands.bot)
    - web.log / web_errors.log - Web panel (Systems.web)
    - core.log / core_errors.log - Core system (Systems.core, Systems.cli)
    - modules.log / modules_errors.log - Modules (module.*, Modules.*)
    - app.log / app_errors.log - Everything else (fallback)
    
    All logs also go to console.
    
    Args:
        name: Logger name (typically module name, e.g. __name__)
        log_level: Optional logging level override (applies to console handler only)
        
    Returns:
        Logger instance (child of root logger)
    
    Example:
        ```python
        logger = get_logger(__name__)
        logger.info("This goes to category log file and console")
        logger.error("This also goes to category_errors.log")
        ```
    """
    # Initialize root logger if not already done
    if not _root_logger_initialized:
        _setup_root_logger()
    
    # Get or create child logger
    logger = logging.getLogger(name)
    
    # Set level if provided (this affects filtering, but handlers have their own levels)
    if log_level:
        numeric_level = getattr(logging, log_level.upper(), logging.INFO)
        logger.setLevel(numeric_level)
    
    # Don't propagate to root if it's a child logger (prevents duplicate logs)
    # Actually, we want propagation for centralized logging
    logger.propagate = True
    
    return logger

