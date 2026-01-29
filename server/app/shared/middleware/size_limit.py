"""
Request Size Limit Middleware for Aiviue Platform.

Prevents abuse by rejecting requests that exceed the maximum allowed size.

Default limit: 1MB (configurable)

Usage:
    app.add_middleware(RequestSizeLimitMiddleware, max_size=1024 * 1024)
"""

from typing import Callable, Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.shared.logging import get_logger


logger = get_logger(__name__)


# Default max size: 1MB
DEFAULT_MAX_SIZE = 1 * 1024 * 1024  # 1MB in bytes


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware that enforces request body size limits.
    
    Checks Content-Length header and rejects if too large.
    
    Args:
        app: ASGI application
        max_size: Maximum allowed body size in bytes (default: 1MB)
    
    Behavior:
    1. GET/HEAD/OPTIONS requests are always allowed (no body)
    2. Check Content-Length header
    3. If exceeds max_size, return 413 Payload Too Large
    4. If no Content-Length, allow but log warning
    """
    
    def __init__(
        self,
        app,
        max_size: int = DEFAULT_MAX_SIZE,
    ) -> None:
        super().__init__(app)
        self.max_size = max_size
        self.max_size_mb = max_size / (1024 * 1024)
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        # Skip for methods without body
        if request.method in ("GET", "HEAD", "OPTIONS", "DELETE"):
            return await call_next(request)
        
        # Get Content-Length header
        content_length = request.headers.get("Content-Length")
        
        if content_length:
            try:
                size = int(content_length)
                
                if size > self.max_size:
                    size_mb = size / (1024 * 1024)
                    
                    logger.warning(
                        f"Request rejected: payload too large ({size_mb:.2f}MB > {self.max_size_mb:.2f}MB)",
                        extra={
                            "event": "request_size_exceeded",
                            "content_length": size,
                            "max_size": self.max_size,
                            "path": request.url.path,
                            "method": request.method,
                        },
                    )
                    
                    return JSONResponse(
                        status_code=413,
                        content={
                            "error": {
                                "type": "VALIDATION_ERROR",
                                "code": "PAYLOAD_TOO_LARGE",
                                "message": f"Request body too large. Maximum allowed size is {self.max_size_mb:.0f}MB",
                            }
                        },
                    )
            except ValueError:
                # Invalid Content-Length header, let it through
                # The server will handle it appropriately
                pass
        else:
            # No Content-Length header for POST/PUT/PATCH
            # This is unusual but not necessarily an error
            # Transfer-Encoding: chunked requests don't have Content-Length
            pass
        
        return await call_next(request)


def get_max_size_from_env() -> int:
    """
    Get max request size from environment variable.
    
    Environment variable: MAX_REQUEST_SIZE_MB (in megabytes)
    Default: 1MB
    """
    import os
    
    try:
        size_mb = int(os.getenv("MAX_REQUEST_SIZE_MB", "1"))
        return size_mb * 1024 * 1024
    except ValueError:
        return DEFAULT_MAX_SIZE
