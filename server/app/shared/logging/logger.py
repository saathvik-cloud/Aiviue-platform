"""
Structured JSON Logger for Aiviue Platform.

Features:
- JSON formatted logs for production (easy to parse)
- Human readable logs for development
- Request context (request_id, employer_id, etc.)
- Automatic timestamp, level, module info

Usage:
    from app.shared.logging import get_logger, setup_logging
    
    # At app startup
    setup_logging()
    
    # In any module
    logger = get_logger(__name__)
    logger.info("User created", extra={"user_id": "123"})
"""

import json
import logging
import sys
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any, Optional

from app.config import settings


# Context variable for request-scoped data
_log_context: ContextVar[dict[str, Any]] = ContextVar("log_context", default={})


class LogContext:
    """
    Context manager for setting log context.
    
    Usage:
        with LogContext(request_id="abc", employer_id="123"):
            logger.info("Processing")  # Automatically includes request_id & employer_id
    """
    
    def __init__(self, **kwargs: Any) -> None:
        self.new_context = kwargs
        self.previous_context: dict[str, Any] = {}
    
    def __enter__(self) -> "LogContext":
        self.previous_context = _log_context.get().copy()
        merged = {**self.previous_context, **self.new_context}
        _log_context.set(merged)
        return self
    
    def __exit__(self, *args: Any) -> None:
        _log_context.set(self.previous_context)


def set_log_context(**kwargs: Any) -> None:
    """Set log context values (persists until cleared)."""
    current = _log_context.get().copy()
    current.update(kwargs)
    _log_context.set(current)


def get_log_context() -> dict[str, Any]:
    """Get current log context."""
    return _log_context.get().copy()


def clear_log_context() -> None:
    """Clear all log context."""
    _log_context.set({})


class JSONFormatter(logging.Formatter):
    """
    JSON log formatter for production.
    
    Output format:
    {
        "timestamp": "2024-01-15T10:30:00.123Z",
        "level": "INFO",
        "logger": "app.domains.employer.services",
        "message": "Employer created",
        "request_id": "abc-123",
        "employer_id": "456",
        "duration_ms": 45
    }
    """
    
    def format(self, record: logging.LogRecord) -> str:
        # Base log entry
        log_entry: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add context from contextvars
        context = _log_context.get()
        if context:
            log_entry.update(context)
        
        # Add extra fields from log call
        # Skip standard LogRecord attributes
        skip_attrs = {
            "name", "msg", "args", "created", "filename", "funcName",
            "levelname", "levelno", "lineno", "module", "msecs",
            "pathname", "process", "processName", "relativeCreated",
            "stack_info", "exc_info", "exc_text", "thread", "threadName",
            "taskName", "message",
        }
        
        for key, value in record.__dict__.items():
            if key not in skip_attrs and not key.startswith("_"):
                # Handle non-serializable values
                try:
                    json.dumps(value)
                    log_entry[key] = value
                except (TypeError, ValueError):
                    log_entry[key] = str(value)
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry, default=str)


class DevelopmentFormatter(logging.Formatter):
    """
    Human-readable formatter for development.
    
    Output format:
    2024-01-15 10:30:00 | INFO     | app.services | Employer created | request_id=abc-123
    """
    
    COLORS = {
        "DEBUG": "\033[36m",     # Cyan
        "INFO": "\033[32m",      # Green
        "WARNING": "\033[33m",   # Yellow
        "ERROR": "\033[31m",     # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"
    
    def format(self, record: logging.LogRecord) -> str:
        # Timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Colored level
        color = self.COLORS.get(record.levelname, "")
        level = f"{color}{record.levelname:8}{self.RESET}"
        
        # Logger name (shortened)
        logger_name = record.name
        if logger_name.startswith("app."):
            logger_name = logger_name[4:]  # Remove "app." prefix
        if len(logger_name) > 30:
            logger_name = "..." + logger_name[-27:]
        
        # Message
        message = record.getMessage()
        
        # Context from contextvars
        context_parts = []
        context = _log_context.get()
        for key, value in context.items():
            context_parts.append(f"{key}={value}")
        
        # Extra fields
        skip_attrs = {
            "name", "msg", "args", "created", "filename", "funcName",
            "levelname", "levelno", "lineno", "module", "msecs",
            "pathname", "process", "processName", "relativeCreated",
            "stack_info", "exc_info", "exc_text", "thread", "threadName",
            "taskName", "message",
        }
        
        for key, value in record.__dict__.items():
            if key not in skip_attrs and not key.startswith("_"):
                context_parts.append(f"{key}={value}")
        
        # Build final message
        parts = [timestamp, level, f"{logger_name:30}", message]
        if context_parts:
            parts.append(" | ".join(context_parts))
        
        formatted = " | ".join(parts)
        
        # Add exception if present
        if record.exc_info:
            formatted += "\n" + self.formatException(record.exc_info)
        
        return formatted


def setup_logging(
    level: Optional[str] = None,
    json_format: Optional[bool] = None,
) -> None:
    """
    Setup logging configuration.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR). Defaults to settings.log_level
        json_format: Use JSON format. Defaults to True in production, False in development
    
    Call once at application startup:
        setup_logging()
    """
    log_level = level or settings.log_level
    use_json = json_format if json_format is not None else settings.is_production
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Create handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    
    # Set formatter based on environment
    if use_json:
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(DevelopmentFormatter())
    
    root_logger.addHandler(handler)
    
    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.
    
    Usage:
        logger = get_logger(__name__)
        logger.info("Something happened", extra={"user_id": "123"})
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)
