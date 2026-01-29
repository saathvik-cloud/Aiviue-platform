"""
Utilities module for Aiviue Platform.

Provides common utility functions used across the application.

Usage:
    from app.shared.utils import sanitize_text, sanitize_dict
    from app.shared.utils import PaginationParams, encode_cursor
    
    clean_input = sanitize_text(user_input)
"""

from app.shared.utils.sanitize import (
    sanitize_text,
    sanitize_dict,
    sanitize_list,
    sanitize_email,
    sanitize_phone,
    is_safe_string,
)
from app.shared.utils.pagination import (
    PaginationParams,
    PaginatedResponse,
    CursorData,
    encode_cursor,
    decode_cursor,
    create_paginated_response,
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
)

__all__ = [
    # Sanitization
    "sanitize_text",
    "sanitize_dict",
    "sanitize_list",
    "sanitize_email",
    "sanitize_phone",
    "is_safe_string",
    # Pagination
    "PaginationParams",
    "PaginatedResponse",
    "CursorData",
    "encode_cursor",
    "decode_cursor",
    "create_paginated_response",
    "DEFAULT_PAGE_SIZE",
    "MAX_PAGE_SIZE",
]
