"""
Resume Extraction Service for Candidate Module.

Extracts structured data from uploaded resume PDFs using:
1. PyMuPDF (fitz) for PDF text extraction
2. Gemini LLM for structured data parsing (role-aware)
3. Normalization layer for consistent field formats
4. Missing field detection against role question templates

Production patterns:
- Pipeline pattern (extract → parse → normalize → detect missing)
- Dictionary dispatch for field normalization
- Same ExtractionResult dataclass as JD extraction (consistency)
- Graceful fallback on extraction failures
"""

import io
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set
from uuid import UUID

from app.domains.job_master.models import RoleQuestionTemplate
from app.shared.llm.client import GeminiClient, LLMError, get_gemini_client
from app.shared.llm.prompts import (
    RESUME_PARSE_SYSTEM_PROMPT,
    build_resume_parse_prompt,
)
from app.shared.logging import get_logger


logger = get_logger(__name__)


# ==================== RESULT DATACLASS ====================

@dataclass
class ResumeExtractionResult:
    """
    Result of a resume extraction operation.

    Mirrors ExtractionResult from JD extraction for consistency.
    """
    success: bool
    extracted_data: Optional[Dict[str, Any]] = None
    missing_keys: List[str] = field(default_factory=list)
    extracted_keys: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    error_type: Optional[str] = None
    tokens_used: int = 0
    retryable: bool = False
    extraction_confidence: float = 0.0
    resume_quality: str = "unknown"
    raw_text_length: int = 0


# ==================== FIELD NORMALIZERS (Dictionary Dispatch) ====================

def _normalize_string(value: Any) -> Optional[str]:
    """Normalize a string field."""
    if value is None:
        return None
    val = str(value).strip()
    return val if val else None


def _normalize_number(value: Any) -> Optional[float]:
    """Normalize a number field."""
    if value is None:
        return None
    try:
        num = float(value)
        return int(num) if num == int(num) else num
    except (ValueError, TypeError):
        return None


def _normalize_boolean(value: Any) -> Optional[bool]:
    """Normalize a boolean field."""
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in ("true", "yes", "1", "y")
    return bool(value)


def _normalize_list(value: Any) -> Optional[list]:
    """Normalize a list field."""
    if value is None:
        return None
    if isinstance(value, list):
        cleaned = [str(v).strip() for v in value if v and str(v).strip()]
        return cleaned if cleaned else None
    if isinstance(value, str):
        items = [v.strip() for v in value.split(",") if v.strip()]
        return items if items else None
    return None


def _normalize_date(value: Any) -> Optional[str]:
    """Normalize a date field to YYYY-MM-DD."""
    if value is None:
        return None
    val = str(value).strip()
    if not val:
        return None
    # Already in correct format
    if len(val) == 10 and val[4] == "-" and val[7] == "-":
        return val
    # Try common formats
    from datetime import datetime
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d", "%m/%d/%Y"):
        try:
            parsed = datetime.strptime(val, fmt)
            return parsed.strftime("%Y-%m-%d")
        except ValueError:
            continue
    return val  # Return as-is if can't parse


# Question type → normalizer mapping
FIELD_NORMALIZERS: Dict[str, callable] = {
    "text": _normalize_string,
    "number": _normalize_number,
    "boolean": _normalize_boolean,
    "select": _normalize_string,
    "multi_select": _normalize_list,
    "date": _normalize_date,
    "file": _normalize_string,
}

# Question key → expected type (for normalization without template)
KEY_TYPE_HINTS: Dict[str, str] = {
    "full_name": "text",
    "date_of_birth": "date",
    "email": "text",
    "phone": "text",
    "preferred_location": "text",
    "languages_known": "multi_select",
    "education": "text",
    "skills": "multi_select",
    "experience_years": "number",
    "experience_details": "text",
    "salary_expectation": "number",
    "has_driving_license": "boolean",
    "owns_vehicle": "boolean",
    "vehicle_type": "text",
    "license_type": "text",
    "portfolio_url": "text",
    "about": "text",
    "preferred_work_type": "text",
    "preferred_shift": "text",
    "computer_skills": "boolean",
    "physical_fitness": "boolean",
}


# ==================== PDF TEXT EXTRACTOR ====================

class PDFTextExtractor:
    """
    Extracts text from PDF files using PyMuPDF (fitz).

    Handles:
    - Multi-page PDFs
    - Text extraction with layout preservation
    - Truncation for very large documents
    - Graceful error handling for corrupt/unsupported PDFs
    """

    MAX_TEXT_LENGTH = 20000  # ~5k tokens, sufficient for resume

    @staticmethod
    def extract_from_bytes(pdf_bytes: bytes) -> str:
        """
        Extract text from PDF bytes.

        Args:
            pdf_bytes: Raw PDF file content

        Returns:
            Extracted text string

        Raises:
            ValueError: If PDF is empty or unreadable
        """
        try:
            import fitz  # PyMuPDF
        except ImportError:
            raise ImportError(
                "PyMuPDF is required for PDF extraction. "
                "Install with: pip install PyMuPDF"
            )

        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        except Exception as e:
            raise ValueError(f"Could not open PDF: {str(e)}")

        if doc.page_count == 0:
            raise ValueError("PDF has no pages")

        text_parts = []
        for page_num in range(doc.page_count):
            page = doc[page_num]
            page_text = page.get_text("text")
            if page_text.strip():
                text_parts.append(page_text)

        doc.close()

        full_text = "\n\n".join(text_parts)
        
        # Sanitize text to prevent interference with LLM prompt structure
        full_text = full_text.replace("```", "''")

        if not full_text.strip():
            raise ValueError(
                "No text could be extracted from the PDF. "
                "The PDF may contain only images or scanned content."
            )

        # Truncate if too long
        if len(full_text) > PDFTextExtractor.MAX_TEXT_LENGTH:
            logger.warning(
                f"PDF text truncated from {len(full_text)} to {PDFTextExtractor.MAX_TEXT_LENGTH} chars"
            )
            full_text = full_text[:PDFTextExtractor.MAX_TEXT_LENGTH] + "\n... [truncated]"

        return full_text

    @staticmethod
    def extract_from_url(pdf_url: str) -> str:
        """
        Download PDF from URL and extract text.

        NOTE: This is a synchronous method. For async, use extract_from_url_async.

        Args:
            pdf_url: URL to the PDF file

        Returns:
            Extracted text string
        """
        import httpx

        try:
            response = httpx.get(pdf_url, timeout=30.0, follow_redirects=True)
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise ValueError(f"Could not download PDF from URL: {str(e)}")

        return PDFTextExtractor.extract_from_bytes(response.content)

    @staticmethod
    async def extract_from_url_async(pdf_url: str) -> str:
        """
        Async download PDF from URL and extract text.

        Args:
            pdf_url: URL to the PDF file

        Returns:
            Extracted text string
        """
        import httpx

        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                response = await client.get(pdf_url)
                response.raise_for_status()
        except httpx.HTTPError as e:
            raise ValueError(f"Could not download PDF from URL: {str(e)}")

        return PDFTextExtractor.extract_from_bytes(response.content)


# ==================== RESUME EXTRACTION SERVICE ====================

class ResumeExtractionService:
    """
    End-to-end resume extraction pipeline.

    Pipeline: PDF → Text → LLM Parse → Normalize → Detect Missing Fields

    Follows the same pattern as JDExtractor but with:
    - Role-aware extraction (question keys aligned to role templates)
    - Missing field detection for dynamic follow-up questions
    - Normalization layer for consistent data types
    """

    def __init__(
        self,
        llm_client: Optional[GeminiClient] = None,
        temperature: float = 0.0,
        max_tokens: int = 3000,
    ) -> None:
        self._client = llm_client or get_gemini_client()
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._pdf_extractor = PDFTextExtractor()

    # ==================== PUBLIC API ====================

    async def extract_from_pdf_url(
        self,
        pdf_url: str,
        role_name: Optional[str] = None,
        job_type: Optional[str] = None,
        question_templates: Optional[List[RoleQuestionTemplate]] = None,
    ) -> ResumeExtractionResult:
        """
        Full extraction pipeline from PDF URL.

        Steps:
        1. Download + extract text from PDF
        2. Send text to LLM for structured parsing
        3. Normalize extracted fields
        4. Detect missing required fields vs role templates

        Args:
            pdf_url: URL to the resume PDF
            role_name: Target job role (for context-aware extraction)
            job_type: blue_collar / white_collar
            question_templates: Role question templates (for missing field detection)

        Returns:
            ResumeExtractionResult with extracted data and missing keys
        """
        # Step 1: Extract text from PDF
        try:
            raw_text = await PDFTextExtractor.extract_from_url_async(pdf_url)
        except ValueError as e:
            logger.error(f"PDF text extraction failed: {e}")
            return ResumeExtractionResult(
                success=False,
                error_message=str(e),
                error_type="pdf_extraction_error",
                retryable=False,
            )
        except ImportError as e:
            logger.error(f"PDF library not available: {e}")
            return ResumeExtractionResult(
                success=False,
                error_message=str(e),
                error_type="dependency_error",
                retryable=False,
            )

        return await self.extract_from_text(
            raw_text=raw_text,
            role_name=role_name,
            job_type=job_type,
            question_templates=question_templates,
        )

    async def extract_from_pdf_bytes(
        self,
        pdf_bytes: bytes,
        role_name: Optional[str] = None,
        job_type: Optional[str] = None,
        question_templates: Optional[List[RoleQuestionTemplate]] = None,
    ) -> ResumeExtractionResult:
        """
        Full extraction pipeline from PDF bytes.

        Args:
            pdf_bytes: Raw PDF file content
            role_name, job_type, question_templates: Same as extract_from_pdf_url

        Returns:
            ResumeExtractionResult
        """
        try:
            raw_text = PDFTextExtractor.extract_from_bytes(pdf_bytes)
        except (ValueError, ImportError) as e:
            logger.error(f"PDF text extraction failed: {e}")
            return ResumeExtractionResult(
                success=False,
                error_message=str(e),
                error_type="pdf_extraction_error",
                retryable=False,
            )

        return await self.extract_from_text(
            raw_text=raw_text,
            role_name=role_name,
            job_type=job_type,
            question_templates=question_templates,
        )

    async def extract_from_text(
        self,
        raw_text: str,
        role_name: Optional[str] = None,
        job_type: Optional[str] = None,
        question_templates: Optional[List[RoleQuestionTemplate]] = None,
    ) -> ResumeExtractionResult:
        """
        Extract structured data from raw resume text.

        Steps:
        2. LLM parsing
        3. Normalization
        4. Missing field detection

        Args:
            raw_text: Raw text from PDF
            role_name, job_type: For context-aware extraction
            question_templates: For missing field detection

        Returns:
            ResumeExtractionResult
        """
        if not raw_text or not raw_text.strip():
            return ResumeExtractionResult(
                success=False,
                error_message="Empty resume text",
                error_type="validation_error",
                retryable=False,
            )

        # Build target question keys from templates
        target_keys = None
        if question_templates:
            target_keys = [t.question_key for t in question_templates if t.is_active]

        # Step 2: LLM parsing
        try:
            llm_result = await self._call_llm(
                raw_text=raw_text,
                target_keys=target_keys,
                role_name=role_name,
                job_type=job_type,
            )
        except LLMError as e:
            logger.error(f"LLM resume parsing failed: {e}")
            return ResumeExtractionResult(
                success=False,
                error_message=str(e.message),
                error_type=e.error_type.value,
                retryable=e.retryable,
            )
        except Exception as e:
            logger.exception(f"Unexpected error in LLM parsing: {e}")
            return ResumeExtractionResult(
                success=False,
                error_message=f"Unexpected error: {str(e)}",
                error_type="unknown",
                retryable=True,
            )

        # Step 3: Normalize extracted data
        extracted_data = llm_result.get("extracted_data", {})
        normalized_data = self._normalize_extracted_data(
            extracted_data, question_templates
        )

        # Step 4: Detect missing fields
        extracted_keys = [
            k for k, v in normalized_data.items() if v is not None
        ]
        missing_keys = self._detect_missing_fields(
            normalized_data, question_templates
        )

        confidence = llm_result.get("extraction_confidence", 0.5)
        quality = llm_result.get("resume_quality", "moderate")

        logger.info(
            "Resume extraction successful",
            extra={
                "extracted_count": len(extracted_keys),
                "missing_count": len(missing_keys),
                "confidence": confidence,
                "quality": quality,
                "text_length": len(raw_text),
            },
        )

        return ResumeExtractionResult(
            success=True,
            extracted_data=normalized_data,
            missing_keys=missing_keys,
            extracted_keys=extracted_keys,
            extraction_confidence=confidence,
            resume_quality=quality,
            raw_text_length=len(raw_text),
        )

    # ==================== INTERNAL: LLM CALL ====================

    async def _call_llm(
        self,
        raw_text: str,
        target_keys: Optional[List[str]] = None,
        role_name: Optional[str] = None,
        job_type: Optional[str] = None,
    ) -> dict:
        """Call LLM for structured resume parsing."""
        prompt = build_resume_parse_prompt(
            resume_text=raw_text,
            target_question_keys=target_keys,
            role_name=role_name,
            job_type=job_type,
        )

        response = await self._client.generate(
            prompt=prompt,
            system_instruction=RESUME_PARSE_SYSTEM_PROMPT,
            temperature=self._temperature,
            max_tokens=self._max_tokens,
        )

        return self._client._parse_json(response.content)

    # ==================== INTERNAL: NORMALIZATION ====================

    def _normalize_extracted_data(
        self,
        extracted_data: Dict[str, Any],
        question_templates: Optional[List[RoleQuestionTemplate]] = None,
    ) -> Dict[str, Any]:
        """
        Normalize extracted data using dictionary dispatch.

        Uses question template types when available, falls back to KEY_TYPE_HINTS.
        """
        # Build key → type map from templates
        key_type_map: Dict[str, str] = dict(KEY_TYPE_HINTS)  # defaults
        if question_templates:
            for template in question_templates:
                key_type_map[template.question_key] = template.question_type

        normalized = {}
        for key, value in extracted_data.items():
            if value is None:
                continue

            field_type = key_type_map.get(key, "text")
            normalizer = FIELD_NORMALIZERS.get(field_type, _normalize_string)
            normalized_value = normalizer(value)

            if normalized_value is not None:
                normalized[key] = normalized_value

        return normalized

    # ==================== INTERNAL: MISSING FIELD DETECTION ====================

    def _detect_missing_fields(
        self,
        normalized_data: Dict[str, Any],
        question_templates: Optional[List[RoleQuestionTemplate]] = None,
    ) -> List[str]:
        """
        Detect which required fields are missing from the extracted data.

        Only checks against role question templates. Fields not in templates
        are not considered "missing" (they're bonus data).

        Returns:
            List of missing question_keys that are required
        """
        if not question_templates:
            return []

        missing = []
        for template in question_templates:
            if not template.is_active:
                continue
            if not template.is_required:
                continue

            # Check conditions (skip conditional questions whose dependency is missing)
            if template.condition:
                depends_on = template.condition.get("depends_on")
                expected_value = template.condition.get("value")
                if depends_on:
                    actual_value = normalized_data.get(depends_on)
                    if actual_value != expected_value:
                        continue  # Condition not met, this question is skipped

            # Check if key is present in extracted data
            if template.question_key not in normalized_data:
                missing.append(template.question_key)

        return missing


# ==================== FACTORY ====================

_extractor: Optional[ResumeExtractionService] = None


def get_resume_extractor() -> ResumeExtractionService:
    """Get or create global resume extractor."""
    global _extractor
    if _extractor is None:
        _extractor = ResumeExtractionService()
    return _extractor
