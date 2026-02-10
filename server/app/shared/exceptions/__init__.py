"""
Exceptions module for Aiviue Platform.

Usage:
    from app.shared.exceptions import NotFoundError, ValidationError
    
    raise NotFoundError(
        message="Employer not found",
        error_code="EMPLOYER_NOT_FOUND"
    )

Register handlers in main.py:
    from app.shared.exceptions import register_exception_handlers
    
    app = FastAPI()
    register_exception_handlers(app)
"""

from app.shared.exceptions.base import (
    BaseAppException,
    BusinessError,
    ConflictError,
    ForbiddenError,
    InfraError,
    NotFoundError,
    RateLimitError,
    ValidationError,
)
from app.shared.exceptions.handlers import register_exception_handlers

__all__ = [
    # Exception classes
    "BaseAppException",
    "ValidationError",
    "NotFoundError",
    "ConflictError",
    "ForbiddenError",
    "BusinessError",
    "InfraError",
    "RateLimitError",
    # Handler registration
    "register_exception_handlers",
]
