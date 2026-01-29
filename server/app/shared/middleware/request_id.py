"""
Request ID Middleware for Aiviue Platform.

Generates a unique request ID for each incoming request.
This ID is used for:
- Tracing requests across logs
- Debugging and error tracking
- Correlation in distributed systems

Usage:
    app.add_middleware(RequestIDMiddleware)
    
    # In routes/services:
    request_id = request.state.request_id
"""

import uuid
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.shared.logging import set_log_context, clear_log_context


# Header name for request ID
REQUEST_ID_HEADER = "X-Request-ID"


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware that assigns a unique ID to each request.
    
    Behavior:
    1. Check if client sent X-Request-ID header
    2. If yes, use that ID (allows tracing from frontend)
    3. If no, generate a new UUID
    4. Store in request.state.request_id
    5. Add X-Request-ID header to response
    6. Set in log context for automatic inclusion in logs
    """
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        # Get existing request ID from header or generate new one
        request_id = request.headers.get(REQUEST_ID_HEADER)
        
        if not request_id:
            request_id = str(uuid.uuid4())
        
        # Store in request state for access in routes/services
        request.state.request_id = request_id
        
        # Set in log context so all logs include request_id
        set_log_context(request_id=request_id)
        
        try:
            # Process request
            response = await call_next(request)
            
            # Add request ID to response headers
            response.headers[REQUEST_ID_HEADER] = request_id
            
            return response
        finally:
            # Clear log context after request completes
            clear_log_context()


def get_request_id(request: Request) -> str | None:
    """
    Get request ID from request state.
    
    Utility function to safely get request_id from request.
    
    Args:
        request: FastAPI/Starlette Request object
    
    Returns:
        Request ID string or None if not set
    """
    return getattr(request.state, "request_id", None)
