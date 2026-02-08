"""
Input Sanitization Utilities for Aiviue Platform.

Provides functions to clean and sanitize user input to prevent:
- XSS attacks (HTML/script injection)
- SQL injection (handled by SQLAlchemy, but extra safety)
- Control characters
- Excessive whitespace

Usage:
    from app.shared.utils.sanitize import sanitize_text, sanitize_dict
    
    clean_name = sanitize_text(user_input)
    clean_data = sanitize_dict(request_data)
"""

import html
import re
from typing import Any, Optional


# Regex patterns for sanitization
SCRIPT_PATTERN = re.compile(r'<script[^>]*>.*?</script>', re.IGNORECASE | re.DOTALL)
STYLE_PATTERN = re.compile(r'<style[^>]*>.*?</style>', re.IGNORECASE | re.DOTALL)
HTML_TAG_PATTERN = re.compile(r'<[^>]+>')
HTML_COMMENT_PATTERN = re.compile(r'<!--.*?-->', re.DOTALL)
CONTROL_CHAR_PATTERN = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]')
MULTIPLE_SPACES_PATTERN = re.compile(r' {2,}')
MULTIPLE_NEWLINES_PATTERN = re.compile(r'\n{3,}')


def sanitize_text(
    text: Optional[str],
    *,
    strip_html: bool = True,
    strip_scripts: bool = True,
    strip_control_chars: bool = True,
    normalize_whitespace: bool = True,
    max_length: Optional[int] = None,
    preserve_newlines: bool = True,
) -> Optional[str]:
    """
    Sanitize a text string by removing potentially dangerous content.
    
    Args:
        text: Input text to sanitize
        strip_html: Remove HTML tags
        strip_scripts: Remove script and style tags
        strip_control_chars: Remove control characters
        normalize_whitespace: Collapse multiple spaces/newlines
        max_length: Truncate to max length if specified
        preserve_newlines: Keep newlines when normalizing (for JD text)
    
    Returns:
        Sanitized text or None if input was None
    
    Example:
        >>> sanitize_text("<script>alert('xss')</script>Hello")
        'Hello'
        >>> sanitize_text("  Multiple   spaces  ")
        'Multiple spaces'
    """
    if text is None:
        return None
    
    if not isinstance(text, str):
        text = str(text)
    
    result = text
    
    # Remove script tags first (most dangerous)
    if strip_scripts:
        result = SCRIPT_PATTERN.sub('', result)
        result = STYLE_PATTERN.sub('', result)
    
    # Remove HTML comments
    result = HTML_COMMENT_PATTERN.sub('', result)
    
    # Remove HTML tags
    if strip_html:
        result = HTML_TAG_PATTERN.sub('', result)
        # Decode HTML entities (e.g., &amp; -> &)
        result = html.unescape(result)
    
    # Remove control characters (keep newlines and tabs if preserving)
    if strip_control_chars:
        result = CONTROL_CHAR_PATTERN.sub('', result)
    
    # Normalize whitespace
    if normalize_whitespace:
        # Collapse multiple spaces
        result = MULTIPLE_SPACES_PATTERN.sub(' ', result)
        
        if preserve_newlines:
            # Collapse more than 2 consecutive newlines to 2
            result = MULTIPLE_NEWLINES_PATTERN.sub('\n\n', result)
        else:
            # Replace all newlines with spaces
            result = result.replace('\n', ' ')
            result = MULTIPLE_SPACES_PATTERN.sub(' ', result)
    
    # Trim leading/trailing whitespace
    result = result.strip()
    
    # Truncate if max_length specified
    if max_length and len(result) > max_length:
        result = result[:max_length].rsplit(' ', 1)[0] + '...'
    
    return result


def sanitize_dict(
    data: dict[str, Any],
    *,
    recursive: bool = True,
    string_fields_only: bool = True,
    skip_fields: Optional[set[str]] = None,
) -> dict[str, Any]:
    """
    Sanitize all string values in a dictionary.
    
    Args:
        data: Dictionary to sanitize
        recursive: Also sanitize nested dictionaries
        string_fields_only: Only sanitize string values
        skip_fields: Set of field names to skip (e.g., {"password", "token"})
    
    Returns:
        New dictionary with sanitized values
    
    Example:
        >>> sanitize_dict({"name": "<b>John</b>", "age": 25})
        {"name": "John", "age": 25}
    """
    skip_fields = skip_fields or set()
    result = {}
    
    for key, value in data.items():
        # Skip specified fields
        if key in skip_fields:
            result[key] = value
            continue
        
        if isinstance(value, str):
            result[key] = sanitize_text(value)
        elif isinstance(value, dict) and recursive:
            result[key] = sanitize_dict(
                value,
                recursive=recursive,
                string_fields_only=string_fields_only,
                skip_fields=skip_fields,
            )
        elif isinstance(value, list) and recursive:
            result[key] = sanitize_list(
                value,
                recursive=recursive,
                skip_fields=skip_fields,
            )
        else:
            result[key] = value
    
    return result


def sanitize_list(
    items: list[Any],
    *,
    recursive: bool = True,
    skip_fields: Optional[set[str]] = None,
) -> list[Any]:
    """
    Sanitize all string values in a list.
    
    Args:
        items: List to sanitize
        recursive: Also sanitize nested dicts/lists
        skip_fields: Set of field names to skip in nested dicts
    
    Returns:
        New list with sanitized values
    """
    result = []
    
    for item in items:
        if isinstance(item, str):
            result.append(sanitize_text(item))
        elif isinstance(item, dict) and recursive:
            result.append(sanitize_dict(
                item,
                recursive=recursive,
                skip_fields=skip_fields,
            ))
        elif isinstance(item, list) and recursive:
            result.append(sanitize_list(
                item,
                recursive=recursive,
                skip_fields=skip_fields,
            ))
        else:
            result.append(item)
    
    return result


# Keys whose values must not appear in logs (case-insensitive)
_SENSITIVE_KEYS = frozenset({
    "password", "token", "api_key", "apikey", "secret", "authorization",
    "secret_key", "encryption_key", "service_role_key", "private_key",
})


def is_sensitive_key(key: str) -> bool:
    """Return True if the key is a known sensitive field name (for redaction)."""
    return key.lower() in _SENSITIVE_KEYS


def redact_sensitive_dict(data: Any) -> Any:
    """
    Return a copy of data with sensitive field values redacted for logging.

    Recursively redacts dict keys that match _SENSITIVE_KEYS (case-insensitive).
    Lists are processed element-wise. Other types are returned as-is.

    Use when logging exception context or request metadata to avoid leaking
    passwords, API keys, or tokens.
    """
    if data is None:
        return None
    if isinstance(data, dict):
        out = {}
        for k, v in data.items():
            key_lower = k.lower() if isinstance(k, str) else k
            if isinstance(key_lower, str) and key_lower in _SENSITIVE_KEYS:
                out[k] = "[REDACTED]"
            else:
                out[k] = redact_sensitive_dict(v)
        return out
    if isinstance(data, list):
        return [redact_sensitive_dict(item) for item in data]
    return data


def sanitize_email(email: Optional[str]) -> Optional[str]:
    """
    Sanitize email address.
    
    - Strips whitespace
    - Converts to lowercase
    - Removes any HTML/scripts
    
    Args:
        email: Email address to sanitize
    
    Returns:
        Sanitized email or None
    """
    if email is None:
        return None
    
    # Basic sanitization
    cleaned = sanitize_text(email, preserve_newlines=False)
    
    if cleaned:
        # Lowercase and strip
        cleaned = cleaned.lower().strip()
        # Remove any spaces (shouldn't be there but just in case)
        cleaned = cleaned.replace(' ', '')
    
    return cleaned


def sanitize_phone(phone: Optional[str]) -> Optional[str]:
    """
    Sanitize phone number.
    
    - Keeps only digits, +, -, (, ), and spaces
    - Removes any HTML/scripts
    
    Args:
        phone: Phone number to sanitize
    
    Returns:
        Sanitized phone or None
    """
    if phone is None:
        return None
    
    # First remove any HTML/scripts
    cleaned = sanitize_text(phone, preserve_newlines=False)
    
    if cleaned:
        # Keep only valid phone characters
        cleaned = re.sub(r'[^\d+\-() ]', '', cleaned)
        # Collapse multiple spaces
        cleaned = MULTIPLE_SPACES_PATTERN.sub(' ', cleaned).strip()
    
    return cleaned if cleaned else None


def is_safe_string(text: str) -> bool:
    """
    Check if a string is safe (no HTML/scripts).
    
    Useful for validation without modifying the string.
    
    Args:
        text: String to check
    
    Returns:
        True if safe, False if contains potential threats
    """
    if not text:
        return True
    
    # Check for script tags
    if SCRIPT_PATTERN.search(text):
        return False
    
    # Check for any HTML tags
    if HTML_TAG_PATTERN.search(text):
        return False
    
    # Check for HTML entities that might be XSS
    dangerous_entities = ['&lt;script', '&lt;img', 'javascript:', 'onerror=', 'onload=']
    text_lower = text.lower()
    for entity in dangerous_entities:
        if entity in text_lower:
            return False
    
    return True
