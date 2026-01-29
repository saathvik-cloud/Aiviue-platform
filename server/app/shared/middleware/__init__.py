"""
Middleware module for Aiviue Platform.

Middleware stack (order matters - first added = outermost):
1. ErrorHandlerMiddleware - Catches all exceptions
2. RequestSizeLimitMiddleware - Rejects large payloads
3. RequestIDMiddleware - Generates request IDs
4. LoggingMiddleware - Logs requests/responses

Usage in main.py:
    from app.shared.middleware import (
        ErrorHandlerMiddleware,
        RequestSizeLimitMiddleware,
        RequestIDMiddleware,
        LoggingMiddleware,
    )
    
    # Add in reverse order (last added runs first)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(RequestSizeLimitMiddleware)
    app.add_middleware(ErrorHandlerMiddleware)
"""

from app.shared.middleware.error_handler import ErrorHandlerMiddleware
from app.shared.middleware.logging import LoggingMiddleware
from app.shared.middleware.request_id import (
    RequestIDMiddleware,
    get_request_id,
    REQUEST_ID_HEADER,
)
from app.shared.middleware.size_limit import (
    RequestSizeLimitMiddleware,
    DEFAULT_MAX_SIZE,
)

__all__ = [
    # Middleware classes
    "ErrorHandlerMiddleware",
    "RequestSizeLimitMiddleware",
    "RequestIDMiddleware",
    "LoggingMiddleware",
    # Utilities
    "get_request_id",
    "REQUEST_ID_HEADER",
    "DEFAULT_MAX_SIZE",
]
