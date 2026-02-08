"""
Cursor-based Pagination Utilities for Aiviue Platform.

Why cursor-based instead of offset-based?
- Offset pagination breaks at scale (OFFSET 100000 is slow)
- Cursor pagination is O(1) regardless of page number
- Consistent results even when data changes

Usage:
    from app.shared.utils.pagination import (
        encode_cursor,
        decode_cursor,
        PaginationParams,
        PaginatedResponse,
    )
    
    # In repository
    cursor_data = decode_cursor(params.cursor)
    items = await self.get_items_after_cursor(cursor_data, params.limit)
    
    # In response
    return PaginatedResponse(
        items=items,
        next_cursor=encode_cursor(items[-1].id, items[-1].created_at),
        has_more=len(items) == params.limit,
    )
"""

import base64
import json
from datetime import datetime
from typing import Any, Generic, Optional, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# Type variable for generic paginated response
T = TypeVar("T")


# Default pagination settings
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


class PaginationParams(BaseModel):
    """
    Pagination parameters from query string.
    
    Usage in route:
        @router.get("/items")
        async def list_items(
            cursor: Optional[str] = None,
            limit: int = Query(default=20, ge=1, le=100),
        ):
            params = PaginationParams(cursor=cursor, limit=limit)
    """
    
    cursor: Optional[str] = Field(
        default=None,
        description="Cursor for pagination (from previous response)",
    )
    limit: int = Field(
        default=DEFAULT_PAGE_SIZE,
        ge=1,
        le=MAX_PAGE_SIZE,
        description=f"Number of items per page (max {MAX_PAGE_SIZE})",
    )


class CursorData(BaseModel):
    """
    Decoded cursor data.
    
    Contains the fields used to determine the next page.
    Typically: id (for uniqueness) + created_at (for ordering)
    """
    
    id: str
    created_at: Optional[datetime] = None
    
    # Additional fields can be added for different sorting
    extra: Optional[dict[str, Any]] = None


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Standard paginated response format.
    
    Response structure:
    {
        "items": [...],
        "pagination": {
            "next_cursor": "abc123...",
            "has_more": true,
            "total_count": 150  // Optional
        }
    }
    """
    
    items: list[T]
    next_cursor: Optional[str] = Field(
        default=None,
        description="Cursor for next page (null if no more items)",
    )
    has_more: bool = Field(
        default=False,
        description="Whether there are more items after this page",
    )
    total_count: Optional[int] = Field(
        default=None,
        description="Total count of items (optional, expensive to compute)",
    )
    
    model_config = ConfigDict(arbitrary_types_allowed=True)


def encode_cursor(
    id: str | UUID,
    created_at: Optional[datetime] = None,
    **extra: Any,
) -> str:
    """
    Encode pagination cursor from ID and timestamp.
    
    Args:
        id: Unique identifier (usually UUID)
        created_at: Timestamp for ordering
        **extra: Additional fields for complex sorting
    
    Returns:
        Base64 encoded cursor string
    
    Example:
        cursor = encode_cursor(
            id="123e4567-e89b-12d3-a456-426614174000",
            created_at=datetime.now()
        )
    """
    cursor_data = {
        "id": str(id),
    }
    
    if created_at:
        cursor_data["created_at"] = created_at.isoformat()
    
    if extra:
        cursor_data["extra"] = extra
    
    # Encode to JSON, then base64
    json_str = json.dumps(cursor_data, default=str)
    encoded = base64.urlsafe_b64encode(json_str.encode()).decode()
    
    return encoded


def decode_cursor(cursor: Optional[str]) -> Optional[CursorData]:
    """
    Decode pagination cursor to extract ID and timestamp.
    
    Args:
        cursor: Base64 encoded cursor string
    
    Returns:
        CursorData object or None if cursor is invalid/None
    
    Example:
        cursor_data = decode_cursor(cursor_string)
        if cursor_data:
            items = await repo.get_after(cursor_data.id, cursor_data.created_at)
    """
    if not cursor:
        return None
    
    try:
        # Decode base64, then JSON
        json_str = base64.urlsafe_b64decode(cursor.encode()).decode()
        data = json.loads(json_str)
        
        # Parse created_at if present
        created_at = None
        if "created_at" in data and data["created_at"]:
            created_at = datetime.fromisoformat(data["created_at"])
        
        return CursorData(
            id=data["id"],
            created_at=created_at,
            extra=data.get("extra"),
        )
    except (ValueError, KeyError, json.JSONDecodeError):
        # Invalid cursor, return None (start from beginning)
        return None


def create_paginated_response(
    items: list[Any],
    limit: int,
    cursor_field: str = "id",
    timestamp_field: str = "created_at",
    total_count: Optional[int] = None,
) -> dict[str, Any]:
    """
    Create a paginated response dictionary.
    
    Helper function to build paginated response from query results.
    
    Args:
        items: List of items (should be limit + 1 to check has_more)
        limit: Requested page size
        cursor_field: Field name for cursor ID (default: "id")
        timestamp_field: Field name for timestamp (default: "created_at")
        total_count: Optional total count
    
    Returns:
        Dictionary with items, next_cursor, has_more, total_count
    
    Example:
        # Query limit + 1 items
        items = await repo.list(limit=params.limit + 1)
        
        # Create response
        return create_paginated_response(
            items=items,
            limit=params.limit,
        )
    """
    # Check if there are more items
    has_more = len(items) > limit
    
    # Trim to requested limit
    if has_more:
        items = items[:limit]
    
    # Generate next cursor from last item
    next_cursor = None
    if has_more and items:
        last_item = items[-1]
        
        # Handle both dict and object
        if isinstance(last_item, dict):
            item_id = last_item.get(cursor_field)
            item_timestamp = last_item.get(timestamp_field)
        else:
            item_id = getattr(last_item, cursor_field, None)
            item_timestamp = getattr(last_item, timestamp_field, None)
        
        if item_id:
            next_cursor = encode_cursor(id=item_id, created_at=item_timestamp)
    
    return {
        "items": items,
        "next_cursor": next_cursor,
        "has_more": has_more,
        "total_count": total_count,
    }
