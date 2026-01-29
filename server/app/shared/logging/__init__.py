"""
Logging module for Aiviue Platform.

Provides structured JSON logging with request context.

Usage:
    from app.shared.logging import get_logger, setup_logging
    
    # Setup once at app startup
    setup_logging()
    
    # Get logger in any module
    logger = get_logger(__name__)
    logger.info("Processing request", extra={"employer_id": "123"})
"""

from app.shared.logging.logger import (
    get_logger,
    setup_logging,
    LogContext,
    set_log_context,
    get_log_context,
    clear_log_context,
)

__all__ = [
    "get_logger",
    "setup_logging",
    "LogContext",
    "set_log_context",
    "get_log_context",
    "clear_log_context",
]
