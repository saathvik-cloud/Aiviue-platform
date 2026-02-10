"""
Custom Exception Classes for Aiviue Platform.

Exception Hierarchy:
- BaseAppException (base class)
  - ValidationError (400) - Invalid input, missing fields
  - NotFoundError (404) - Resource not found
  - ConflictError (409) - Duplicate resource, version mismatch
  - BusinessError (422) - Business rule violation
  - InfraError (500) - Infrastructure failure (DB, Redis, LLM)

Usage:
    raise NotFoundError(
        message="Employer not found",
        error_code="EMPLOYER_NOT_FOUND",
        context={"employer_id": "123"}
    )
"""

from typing import Any, Optional


class BaseAppException(Exception):
    """Base exception class for all application exceptions."""
    
    status_code: int = 500
    error_type: str = "INTERNAL_ERROR"
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        context: Optional[dict[str, Any]] = None,
    ) -> None:
        """
        Initialize the exception.
        
        Args:
            message: Human-readable error message
            error_code: Machine-readable error code (e.g., "EMPLOYER_NOT_FOUND")
            context: Additional context for debugging (not exposed to client in prod)
        """
        self.message = message
        self.error_code = error_code or self.error_type
        self.context = context or {}
        super().__init__(self.message)
    
    def to_dict(self, include_context: bool = False) -> dict[str, Any]:
        """
        Convert exception to dictionary for API response.
        
        Args:
            include_context: Whether to include debug context (only in debug mode)
        
        Returns:
            Dictionary representation of the error
        """
        result = {
            "error": {
                "type": self.error_type,
                "code": self.error_code,
                "message": self.message,
            }
        }
        if include_context and self.context:
            result["error"]["context"] = self.context
        return result


class ValidationError(BaseAppException):
    """
    Raised when input validation fails.
    
    HTTP Status: 400 Bad Request
    
    Examples:
        - Missing required field
        - Invalid email format
        - Value out of range
    """
    
    status_code: int = 400
    error_type: str = "VALIDATION_ERROR"


class NotFoundError(BaseAppException):
    """
    Raised when a requested resource is not found.
    
    HTTP Status: 404 Not Found
    
    Examples:
        - Employer with given ID doesn't exist
        - Job with given ID doesn't exist
    """
    
    status_code: int = 404
    error_type: str = "NOT_FOUND"


class ConflictError(BaseAppException):
    """
    Raised when there's a conflict with existing data.
    
    HTTP Status: 409 Conflict
    
    Examples:
        - Email already exists
        - Optimistic locking failure (version mismatch)
        - Duplicate idempotency key with different payload
    """
    
    status_code: int = 409
    error_type: str = "CONFLICT"


class ForbiddenError(BaseAppException):
    """
    Raised when the user is not allowed to perform the action.
    
    HTTP Status: 403 Forbidden
    
    Examples:
        - Upgrade required to create multiple AIVI bot resumes
        - Access denied to resource
    """
    
    status_code: int = 403
    error_type: str = "FORBIDDEN"


class BusinessError(BaseAppException):
    """
    Raised when a business rule is violated.
    
    HTTP Status: 422 Unprocessable Entity
    
    Examples:
        - Cannot publish job without title
        - Cannot close already closed job
        - Employer not verified
    """
    
    status_code: int = 422
    error_type: str = "BUSINESS_RULE_VIOLATION"


class InfraError(BaseAppException):
    """
    Raised when infrastructure fails.
    
    HTTP Status: 500 Internal Server Error
    
    Examples:
        - Database connection failed
        - Redis connection failed
        - LLM API call failed
        - External service unavailable
    
    Note: These errors are typically retryable.
    """
    
    status_code: int = 500
    error_type: str = "INFRASTRUCTURE_ERROR"


class RateLimitError(BaseAppException):
    """
    Raised when rate limit is exceeded.
    
    HTTP Status: 429 Too Many Requests
    
    Note: Kept for future use when rate limiting is implemented.
    """
    
    status_code: int = 429
    error_type: str = "RATE_LIMIT_EXCEEDED"
