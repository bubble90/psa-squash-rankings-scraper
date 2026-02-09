"""
Centralized logging configuration for PSA Squash scraper.

Provides consistent logging across all modules with proper formatting,
log levels, and file output.
"""

import logging
import sys
from datetime import datetime
from config import LOG_DIR


def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Set up a logger with consistent formatting and handlers.

    Parameters:
    - name: Logger name (usually __name__ from calling module)
    - level: Logging level (default: INFO)

    Returns:
    - Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if logger.handlers:
        return logger

    log_file = LOG_DIR / f"psa_scraper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get or create a logger instance.

    Parameters:
    - name: Logger name (usually __name__ from calling module)

    Returns:
    - Logger instance
    """
    return setup_logger(name)
