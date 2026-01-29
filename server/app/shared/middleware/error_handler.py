"""
Error Handler Middleware for Aiviue Platform.

This middleware is the FIRST line of defense, catching any exceptions
that occur during request processing, including in other middleware.

Note: FastAPI's exception handlers (from handlers.py) handle route-level
exceptions. This middleware catches exceptions from the middleware stack.

Usage:
    app.add_middleware(ErrorHandlerMiddleware)
    
    # IMPORTANT: Add this FIRST so it wraps all other middleware
"""

from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.config import settings
from app.shared.exceptions.base import BaseAppException
from app.shared.logging import get_logger
from app.shared.middleware.request_id import get_request_id


logger = get_logger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    Middleware that catches all unhandled exceptions.
    
    This ensures that even if an exception occurs in another middleware,
    the client receives a proper JSON error response instead of a
    raw error or connection reset.
    
    Placement: Should be the FIRST middleware added (wraps all others).
    
    Handles:
    - Custom application exceptions (BaseAppException)
    - Unexpected exceptions (returns generic 500)
    """
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        try:
            return await call_next(request)
        
        except BaseAppException as exc:
            # Handle our custom exceptions
            request_id = get_request_id(request)
            
            logger.warning(
                f"Application exception: {exc.message}",
                extra={
                    "event": "application_exception",
                    "error_type": exc.error_type,
                    "error_code": exc.error_code,
                    "path": request.url.path,
                    "method": request.method,
                    "context": exc.context,
                },
            )
            
            return self._create_error_response(
                status_code=exc.status_code,
                error_type=exc.error_type,
                error_code=exc.error_code,
                message=exc.message,
                context=exc.context if settings.debug else None,
                request_id=request_id,
            )
        
        except Exception as exc:
            # Handle unexpected exceptions
            request_id = get_request_id(request)
            
            # Log full traceback
            logger.exception(
                f"Unhandled middleware exception: {str(exc)}",
                extra={
                    "event": "unhandled_exception",
                    "exception_type": type(exc).__name__,
                    "path": request.url.path,
                    "method": request.method,
                },
            )
            
            # Don't expose internal details in production
            if settings.debug:
                message = f"Internal error: {str(exc)}"
                context = {
                    "exception_type": type(exc).__name__,
                    "exception_message": str(exc),
                }
            else:
                message = "An unexpected error occurred"
                context = None
            
            return self._create_error_response(
                status_code=500,
                error_type="INTERNAL_ERROR",
                error_code="UNEXPECTED_ERROR",
                message=message,
                context=context,
                request_id=request_id,
            )
    
    def _create_error_response(
        self,
        status_code: int,
        error_type: str,
        error_code: str,
        message: str,
        context: dict | None = None,
        request_id: str | None = None,
    ) -> JSONResponse:
        """Create a standardized JSON error response."""
        error_body = {
            "type": error_type,
            "code": error_code,
            "message": message,
        }
        
        if request_id:
            error_body["request_id"] = request_id
        
        if context:
            error_body["context"] = context
        
        return JSONResponse(
            status_code=status_code,
            content={"error": error_body},
        )
