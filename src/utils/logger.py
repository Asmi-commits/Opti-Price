"""
Centralized logging configuration.
"""

import logging
import sys
from src.utils.config import LOG_LEVEL, LOG_FORMAT


def get_logger(name: str) -> logging.Logger:
    """Create a configured logger instance."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(getattr(logging, LOG_LEVEL.upper(), logging.INFO))
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(handler)
<<<<<<< HEAD
    return logger
=======
    return logger
>>>>>>> 4219dc752222c7785caaafee868265c5ea202b15
