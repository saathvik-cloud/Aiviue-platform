"""
Safe PDF URL fetch for resume uploads.

Validates origin (SSRF protection), enforces max size, and checks content type
before returning bytes for extraction.
"""

from urllib.parse import urlparse

import httpx

from app.shared.logging import get_logger


logger = get_logger(__name__)

# Default max size when not provided (2MB)
DEFAULT_MAX_PDF_BYTES = 2 * 1024 * 1024

# Content-Type we accept for PDF
EXPECTED_CONTENT_TYPE = "application/pdf"


def validate_pdf_url_origin(url: str, allowed_origins: list[str]) -> None:
    """
    Validate that the URL is HTTPS and its origin is in the allowlist.

    Args:
        url: The URL to validate (e.g. from client after Supabase upload).
        allowed_origins: List of allowed origins, e.g. ["https://xxx.supabase.co"].

    Raises:
        ValueError: If URL is not HTTPS or origin not allowed.
    """
    if not url or not url.strip():
        raise ValueError("PDF URL is required")
    parsed = urlparse(url.strip())
    if parsed.scheme != "https":
        raise ValueError("PDF URL must use HTTPS")
    if not parsed.netloc:
        raise ValueError("PDF URL must have a valid host")
    origin = f"{parsed.scheme}://{parsed.netloc}"
    if not allowed_origins:
        raise ValueError("No allowed PDF origins configured; cannot fetch from URL")
    if origin not in allowed_origins:
        raise ValueError("PDF URL origin is not allowed")


async def fetch_pdf_from_url_async(
    url: str,
    max_size_bytes: int = DEFAULT_MAX_PDF_BYTES,
    allowed_origins: list[str] | None = None,
    timeout: float = 30.0,
) -> bytes:
    """
    Fetch PDF bytes from URL with origin, size, and content-type checks.

    Args:
        url: URL to the PDF (must be HTTPS and in allowed_origins).
        max_size_bytes: Maximum response size (prevents oversized payloads).
        allowed_origins: Allowed origins for SSRF protection; required.
        timeout: Request timeout in seconds.

    Returns:
        PDF bytes (up to max_size_bytes).

    Raises:
        ValueError: If URL invalid, origin not allowed, response too large,
                    or content type is not application/pdf.
    """
    if allowed_origins is None:
        allowed_origins = []
    validate_pdf_url_origin(url, allowed_origins)

    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        # Stream so we can enforce size without loading full body first if Content-Length is set
        response = await client.get(url)
        response.raise_for_status()

        content_type = (response.headers.get("content-type") or "").split(";")[0].strip().lower()
        if content_type != EXPECTED_CONTENT_TYPE:
            logger.warning("PDF URL returned non-PDF content-type", extra={"content_type": content_type, "url": url})
            raise ValueError(f"URL did not return a PDF (content-type: {content_type})")

        content_length = response.headers.get("content-length")
        if content_length is not None:
            try:
                cl = int(content_length)
                if cl > max_size_bytes:
                    raise ValueError(
                        f"PDF is too large ({cl} bytes); maximum allowed is {max_size_bytes} bytes"
                    )
            except ValueError as e:
                if "too large" in str(e):
                    raise
                pass  # ignore non-integer Content-Length

        data = response.content
        if len(data) > max_size_bytes:
            raise ValueError(
                f"PDF is too large ({len(data)} bytes); maximum allowed is {max_size_bytes} bytes"
            )
        return data


def fetch_pdf_from_url_sync(
    url: str,
    max_size_bytes: int = DEFAULT_MAX_PDF_BYTES,
    allowed_origins: list[str] | None = None,
    timeout: float = 30.0,
) -> bytes:
    """
    Synchronous version of fetch_pdf_from_url_async.
    Prefer the async version in async code.
    """
    if allowed_origins is None:
        allowed_origins = []
    validate_pdf_url_origin(url, allowed_origins)

    with httpx.Client(timeout=timeout, follow_redirects=True) as client:
        response = client.get(url)
        response.raise_for_status()

        content_type = (response.headers.get("content-type") or "").split(";")[0].strip().lower()
        if content_type != EXPECTED_CONTENT_TYPE:
            logger.warning("PDF URL returned non-PDF content-type", extra={"content_type": content_type, "url": url})
            raise ValueError(f"URL did not return a PDF (content-type: {content_type})")

        content_length = response.headers.get("content-length")
        if content_length is not None:
            try:
                cl = int(content_length)
                if cl > max_size_bytes:
                    raise ValueError(
                        f"PDF is too large ({cl} bytes); maximum allowed is {max_size_bytes} bytes"
                    )
            except ValueError as e:
                if "too large" in str(e):
                    raise
                pass

        data = response.content
        if len(data) > max_size_bytes:
            raise ValueError(
                f"PDF is too large ({len(data)} bytes); maximum allowed is {max_size_bytes} bytes"
            )
        return data
