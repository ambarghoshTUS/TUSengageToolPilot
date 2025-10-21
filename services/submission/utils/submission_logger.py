"""
Logger configuration for submission service

Author: TUS Development Team
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from pythonjsonlogger import jsonlogger


def setup_logger(name, log_level=None):
    """
    Setup logger with both file and console handlers
    
    Args:
        name (str): Logger name
        log_level (str): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        logging.Logger: Configured logger instance
    """
    # Get log level from environment or parameter
    if log_level is None:
        log_level = os.getenv('LOG_LEVEL', 'INFO')
    
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Create logs directory if it doesn't exist
    log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # File handler with rotation
    log_file = os.path.join(log_dir, f'{name}.log')
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(level)
    
    # JSON formatter for structured logging
    json_formatter = jsonlogger.JsonFormatter(
        '%(asctime)s %(name)s %(levelname)s %(message)s'
    )
    file_handler.setFormatter(json_formatter)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    
    # Simple formatter for console
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger
