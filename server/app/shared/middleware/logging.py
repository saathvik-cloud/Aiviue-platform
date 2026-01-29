"""
Logging Middleware for Aiviue Platform.

Logs incoming requests and outgoing responses with timing information.

Logs:
- Request start: method, path, client IP
- Request end: status code, duration in milliseconds

Usage:
    app.add_middleware(LoggingMiddleware)
"""

import time
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.shared.logging import get_logger
from app.shared.middleware.request_id import get_request_id


logger = get_logger(__name__)


# Paths to exclude from logging (health checks, static files)
EXCLUDED_PATHS = {
    "/health",
    "/health/live",
    "/health/ready",
    "/favicon.ico",
    "/docs",
    "/redoc",
    "/openapi.json",
}


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that logs request/response information.
    
    Logs at INFO level:
    - Request start: method, path, client IP
    - Request end: status code, duration
    
    Skips logging for health checks and documentation endpoints.
    """
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        # Skip logging for excluded paths
        if request.url.path in EXCLUDED_PATHS:
            return await call_next(request)
        
        # Get request info
        method = request.method
        path = request.url.path
        query = str(request.query_params) if request.query_params else None
        client_ip = self._get_client_ip(request)
        request_id = get_request_id(request)
        
        # Log request start
        log_data = {
            "event": "request_started",
            "method": method,
            "path": path,
            "client_ip": client_ip,
        }
        if query:
            log_data["query"] = query
        
        logger.info(
            f"→ {method} {path}",
            extra=log_data,
        )
        
        # Process request and measure time
        start_time = time.perf_counter()
        
        try:
            response = await call_next(request)
        except Exception as e:
            # Log exception (will be handled by error handler)
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                f"✗ {method} {path} - Exception",
                extra={
                    "event": "request_failed",
                    "method": method,
                    "path": path,
                    "duration_ms": round(duration_ms, 2),
                    "exception": str(e),
                },
            )
            raise
        
        # Calculate duration
        duration_ms = (time.perf_counter() - start_time) * 1000
        
        # Log request completion
        status_code = response.status_code
        log_level = self._get_log_level(status_code)
        
        status_emoji = self._get_status_emoji(status_code)
        
        logger.log(
            log_level,
            f"{status_emoji} {method} {path} - {status_code} ({duration_ms:.0f}ms)",
            extra={
                "event": "request_completed",
                "method": method,
                "path": path,
                "status_code": status_code,
                "duration_ms": round(duration_ms, 2),
            },
        )
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request, handling proxies."""
        # Check X-Forwarded-For header (set by proxies/load balancers)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # X-Forwarded-For can be comma-separated list, first is client
            return forwarded_for.split(",")[0].strip()
        
        # Check X-Real-IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fall back to direct client
        if request.client:
            return request.client.host
        
        return "unknown"
    
    def _get_log_level(self, status_code: int) -> int:
        """Determine log level based on status code."""
        import logging
        
        if status_code >= 500:
            return logging.ERROR
        elif status_code >= 400:
            return logging.WARNING
        else:
            return logging.INFO
    
    def _get_status_emoji(self, status_code: int) -> str:
        """Get emoji indicator based on status code."""
        if status_code >= 500:
            return "✗"  # Server error
        elif status_code >= 400:
            return "⚠"  # Client error
        elif status_code >= 300:
            return "↪"  # Redirect
        else:
            return "✓"  # Success
