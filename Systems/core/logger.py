"""
Logging configuration module for SwiftDevBot.

This module sets up logging for the entire application with file and console output.
Logs are written to Data/logs/ directory with rotation support.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

from logging.handlers import RotatingFileHandler


def setup_logger(
    log_level: str = "INFO",
    log_dir: Optional[Path] = None,
    module_name: Optional[str] = None
) -> logging.Logger:
    """
    Set up logger with file and console handlers.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files (default: Data/logs/)
        module_name: Name of the module for separate log file
        
    Returns:
        Configured logger instance
    """
    # Determine log directory
    if log_dir is None:
        log_dir = Path("Data/logs")
    else:
        log_dir = Path(log_dir)
    
    # Create log directory if it doesn't exist
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Determine logger name
    logger_name = module_name if module_name else "swiftdevbot"
    logger = logging.getLogger(logger_name)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Set logging level
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    logger.setLevel(numeric_level)
    
    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler with rotation
    log_file = log_dir / f"{logger_name}.log"
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Error file handler (only ERROR and CRITICAL)
    error_log_file = log_dir / f"{logger_name}_errors.log"
    error_handler = RotatingFileHandler(
        error_log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8"
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)
    
    logger.info(f"Logger '{logger_name}' initialized with level {log_level}")
    logger.debug(f"Log files: {log_file}, {error_log_file}")
    
    return logger


def get_logger(name: str, log_level: Optional[str] = None) -> logging.Logger:
    """
    Get or create a logger for a specific module.
    
    Args:
        name: Logger name (typically module name)
        log_level: Optional logging level override
        
    Returns:
        Logger instance
    """
    logger = logging.getLogger(name)
    
    # If logger already has handlers, return it
    if logger.handlers:
        if log_level:
            numeric_level = getattr(logging, log_level.upper(), logging.INFO)
            logger.setLevel(numeric_level)
        return logger
    
    # Otherwise, set up a new logger
    # Try to get log level from root logger or use default
    if log_level is None:
        root_logger = logging.getLogger()
        log_level = logging.getLevelName(root_logger.level) if root_logger.level else "INFO"
    
    return setup_logger(log_level=log_level, module_name=name)

