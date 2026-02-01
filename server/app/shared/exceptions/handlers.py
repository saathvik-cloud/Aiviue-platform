"""
Exception Handlers for FastAPI.

These handlers convert exceptions to proper HTTP responses with
consistent error format.

Usage in main.py:
    from app.shared.exceptions.handlers import register_exception_handlers
    
    app = FastAPI()
    register_exception_handlers(app)
"""

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError

from app.config import settings
from app.shared.exceptions.base import (
    BaseAppException,
    InfraError,
    ValidationError,
)

logger = logging.getLogger(__name__)


def create_error_response(
    status_code: int,
    error_type: str,
    error_code: str,
    message: str,
    context: dict[str, Any] | None = None,
    request_id: str | None = None,
) -> JSONResponse:
    """
    Create a standardized error response.
    
    Response format:
    {
        "error": {
            "type": "VALIDATION_ERROR",
            "code": "INVALID_EMAIL",
            "message": "Invalid email format",
            "request_id": "abc-123",
            "context": {...}  // Only in debug mode
        }
    }
    """
    error_body: dict[str, Any] = {
        "type": error_type,
        "code": error_code,
        "message": message,
    }
    
    # Add request_id if available
    if request_id:
        error_body["request_id"] = request_id
    
    # Add context only in debug mode
    if settings.debug and context:
        error_body["context"] = context
    
    return JSONResponse(
        status_code=status_code,
        content={"error": error_body},
    )


def get_request_id(request: Request) -> str | None:
    """Extract request_id from request state if available."""
    return getattr(request.state, "request_id", None)


async def app_exception_handler(
    request: Request,
    exc: BaseAppException,
) -> JSONResponse:
    """
    Handle all custom application exceptions.
    
    Logs the error and returns a structured response.
    """
    request_id = get_request_id(request)
    
    # Log with appropriate level
    # Note: 'message' is a reserved key in Python logging, use 'error_message' instead
    log_data = {
        "error_type": exc.error_type,
        "error_code": exc.error_code,
        "error_message": exc.message,  # Changed from 'message' to avoid LogRecord conflict
        "request_id": request_id,
        "path": request.url.path,
        "method": request.method,
    }
    
    if exc.context:
        log_data["error_context"] = exc.context  # Changed from 'context'
    
    # Log 5xx as error, others as warning
    if exc.status_code >= 500:
        logger.error(f"Infrastructure error: {exc.message}", extra=log_data)
    else:
        logger.warning(f"Application error: {exc.message}", extra=log_data)
    
    return create_error_response(
        status_code=exc.status_code,
        error_type=exc.error_type,
        error_code=exc.error_code,
        message=exc.message,
        context=exc.context,
        request_id=request_id,
    )


def _serialize_validation_errors(errors: list) -> list:
    """
    Serialize validation errors to ensure they are JSON-compatible.
    
    Pydantic errors may contain non-serializable objects like ValueError.
    """
    serialized = []
    for error in errors:
        serialized_error = {
            "type": error.get("type", "unknown"),
            "loc": list(error.get("loc", [])),
            "msg": str(error.get("msg", "")),
            "input": str(error.get("input", ""))[:100],  # Truncate long inputs
        }
        # Don't include 'ctx' as it may contain non-serializable objects
        serialized.append(serialized_error)
    return serialized


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """
    Handle FastAPI/Pydantic request validation errors.
    
    Converts Pydantic errors to our standard format.
    """
    request_id = get_request_id(request)
    
    # Extract validation error details
    errors = exc.errors()
    
    # Build user-friendly message
    error_details = []
    for error in errors:
        loc = " -> ".join(str(l) for l in error["loc"])
        msg = error["msg"]
        error_details.append(f"{loc}: {msg}")
    
    message = "Validation failed: " + "; ".join(error_details[:3])
    if len(error_details) > 3:
        message += f" (and {len(error_details) - 3} more errors)"
    
    # Serialize errors to avoid JSON serialization issues
    serialized_errors = _serialize_validation_errors(errors)
    
    logger.warning(
        f"Validation error: {message}",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "validation_errors": serialized_errors,  # Changed from 'errors'
        }
    )
    
    return create_error_response(
        status_code=422,  # Changed from 400 to 422 (standard for validation errors)
        error_type="VALIDATION_ERROR",
        error_code="REQUEST_VALIDATION_FAILED",
        message=message,
        context={"errors": serialized_errors} if settings.debug else None,
        request_id=request_id,
    )


async def pydantic_exception_handler(
    request: Request,
    exc: PydanticValidationError,
) -> JSONResponse:
    """
    Handle Pydantic validation errors (non-request validation).
    
    These can occur when validating data in services.
    """
    request_id = get_request_id(request)
    
    errors = exc.errors()
    serialized_errors = _serialize_validation_errors(errors)
    message = f"Data validation failed: {len(errors)} error(s)"
    
    logger.warning(
        f"Pydantic validation error: {message}",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "validation_errors": serialized_errors,
        }
    )
    
    return create_error_response(
        status_code=422,  # Changed from 400 to 422 (standard for validation errors)
        error_type="VALIDATION_ERROR",
        error_code="DATA_VALIDATION_FAILED",
        message=message,
        context={"errors": serialized_errors} if settings.debug else None,
        request_id=request_id,
    )


async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """
    Handle unexpected/unhandled exceptions.
    
    Logs the full traceback and returns a generic error response.
    This is the last line of defense.
    """
    request_id = get_request_id(request)
    
    # Log full traceback for debugging
    logger.exception(
        f"Unhandled exception: {str(exc)}",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "exception_type": type(exc).__name__,
        }
    )
    
    # Don't expose internal error details in production
    message = "An unexpected error occurred"
    context = None
    
    if settings.debug:
        message = f"Internal error: {str(exc)}"
        context = {
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
        }
    
    return create_error_response(
        status_code=500,
        error_type="INTERNAL_ERROR",
        error_code="UNEXPECTED_ERROR",
        message=message,
        context=context,
        request_id=request_id,
    )


def register_exception_handlers(app: FastAPI) -> None:
    """
    Register all exception handlers with the FastAPI app.
    
    Usage:
        app = FastAPI()
        register_exception_handlers(app)
    
    Order matters - more specific handlers first.
    """
    # Custom application exceptions
    app.add_exception_handler(BaseAppException, app_exception_handler)
    
    # FastAPI request validation errors
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    
    # Pydantic validation errors
    app.add_exception_handler(PydanticValidationError, pydantic_exception_handler)
    
    # Catch-all for unhandled exceptions
    app.add_exception_handler(Exception, unhandled_exception_handler)
