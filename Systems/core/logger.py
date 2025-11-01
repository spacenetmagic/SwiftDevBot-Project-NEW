"""
Logging configuration module for SwiftDevBot.

This module sets up logging for the entire application with file and console output.
Logs are written to Data/logs/ directory with rotation support.
Uses grouped logging by category (bot, web, db, modules) instead of per-module files.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

from logging.handlers import RotatingFileHandler

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
    
    if _root_logger_initialized:
        return
    
    # Determine log directory
    if log_dir is None:
        log_dir = Path("Data/logs")
    else:
        log_dir = Path(log_dir)
    
    # Create log directory if it doesn't exist
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Set to lowest level, handlers will filter
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Console handler (all logs to console)
    console_handler = logging.StreamHandler(sys.stdout)
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
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
        category_handler.setFormatter(formatter)
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
        category_error_handler.setFormatter(formatter)
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
    app_file_handler.setFormatter(formatter)
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
    app_error_handler.setFormatter(formatter)
    app_error_handler.addFilter(lambda record: not _matches_any_category(record, categories))
    root_logger.addHandler(app_error_handler)
    
    _root_logger_initialized = True
    log_files = ", ".join([f"{cat}.log, {cat}_errors.log" for cat in categories.keys()])
    root_logger.info(f"Root logger initialized with level {log_level}")
    root_logger.debug(f"Category log files: {log_files}, app.log, app_errors.log")


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

