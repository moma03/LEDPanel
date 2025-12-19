"""
Centralized logging setup for the application.
"""

import logging
import logging.handlers
from pathlib import Path
from .config import settings


def setup_logger(name: str) -> logging.Logger:
    """
    Set up and return a logger instance with console and optional file handlers.
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(settings.LOG_LEVEL.upper())
    
    # Create formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler (always enabled)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(settings.LOG_LEVEL.upper())
    console_handler.setFormatter(formatter)
    
    if not logger.handlers:  # Avoid duplicate handlers
        logger.addHandler(console_handler)
        
        # File handler (if configured)
        if settings.LOG_FILE_PATH:
            log_file = Path(settings.LOG_FILE_PATH)
            log_file.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=10_485_760,  # 10MB
                backupCount=5
            )
            file_handler.setLevel(settings.LOG_LEVEL.upper())
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
    
    return logger


# Module-level logger for this package
logger = setup_logger(__name__)
