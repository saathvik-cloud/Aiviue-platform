"""
Tests for safe PDF URL fetch (origin, size, content-type).

Covers:
- validate_pdf_url_origin: HTTPS only, allowed origins
- fetch_pdf_from_url_async: size limit, content-type check (via mocks)

Run: pytest tests/test_pdf_fetch.py -v
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.shared.utils.pdf_fetch import (
    validate_pdf_url_origin,
    fetch_pdf_from_url_async,
    DEFAULT_MAX_PDF_BYTES,
    EXPECTED_CONTENT_TYPE,
)


class TestValidatePdfUrlOrigin:
    """Validation of PDF URL origin (SSRF protection)."""

    def test_empty_url_raises(self):
        with pytest.raises(ValueError, match="PDF URL is required"):
            validate_pdf_url_origin("", ["https://allowed.example.com"])
        with pytest.raises(ValueError, match="PDF URL is required"):
            validate_pdf_url_origin("   ", ["https://allowed.example.com"])

    def test_http_rejected(self):
        with pytest.raises(ValueError, match="HTTPS"):
            validate_pdf_url_origin(
                "http://example.com/file.pdf",
                ["http://example.com"],
            )

    def test_no_host_rejected(self):
        with pytest.raises(ValueError, match="valid host"):
            validate_pdf_url_origin("https://", ["https://example.com"])

    def test_empty_allowed_origins_raises(self):
        with pytest.raises(ValueError, match="No allowed PDF origins"):
            validate_pdf_url_origin("https://example.com/file.pdf", [])

    def test_disallowed_origin_raises(self):
        with pytest.raises(ValueError, match="origin is not allowed"):
            validate_pdf_url_origin(
                "https://evil.com/resume.pdf",
                ["https://storage.supabase.co"],
            )

    def test_allowed_origin_accepted(self):
        validate_pdf_url_origin(
            "https://storage.supabase.co/storage/v1/object/public/bucket/path.pdf",
            ["https://storage.supabase.co"],
        )

    def test_url_stripped(self):
        validate_pdf_url_origin(
            "  https://storage.supabase.co/file.pdf  ",
            ["https://storage.supabase.co"],
        )


@pytest.mark.asyncio
class TestFetchPdfFromUrlAsync:
    """Safe async fetch: size and content-type enforced."""

    @pytest.fixture
    def allowed_origins(self):
        return ["https://storage.example.com"]

    async def test_content_type_not_pdf_raises(self, allowed_origins):
        mock_response = MagicMock()
        mock_response.headers = {"content-type": "text/html"}
        mock_response.content = b"%PDF-1.4 fake"
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("app.shared.utils.pdf_fetch.httpx") as m_httpx:
            m_httpx.AsyncClient.return_value = mock_client
            with pytest.raises(ValueError, match="did not return a PDF"):
                await fetch_pdf_from_url_async(
                    "https://storage.example.com/fake.pdf",
                    allowed_origins=allowed_origins,
                )

    async def test_response_too_large_raises(self, allowed_origins):
        max_size = 100
        mock_response = MagicMock()
        mock_response.headers = {
            "content-type": EXPECTED_CONTENT_TYPE,
            "content-length": str(max_size + 1),
        }
        mock_response.content = b"x" * (max_size + 1)
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("app.shared.utils.pdf_fetch.httpx") as m_httpx:
            m_httpx.AsyncClient.return_value = mock_client
            with pytest.raises(ValueError, match="too large"):
                await fetch_pdf_from_url_async(
                    "https://storage.example.com/big.pdf",
                    max_size_bytes=max_size,
                    allowed_origins=allowed_origins,
                )

    async def test_success_returns_bytes(self, allowed_origins):
        pdf_bytes = b"%PDF-1.4 minimal"
        mock_response = MagicMock()
        mock_response.headers = {"content-type": EXPECTED_CONTENT_TYPE}
        mock_response.content = pdf_bytes
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("app.shared.utils.pdf_fetch.httpx") as m_httpx:
            m_httpx.AsyncClient.return_value = mock_client
            result = await fetch_pdf_from_url_async(
                "https://storage.example.com/resume.pdf",
                max_size_bytes=DEFAULT_MAX_PDF_BYTES,
                allowed_origins=allowed_origins,
            )
        assert result == pdf_bytes
