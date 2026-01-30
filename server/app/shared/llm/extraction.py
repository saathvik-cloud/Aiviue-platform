"""
LLM Extraction Service for Aiviue Platform.

High-level service for extracting structured data from text using LLM.
"""

from typing import Any, Optional
from dataclasses import dataclass

from app.shared.logging import get_logger
from app.shared.llm.client import GeminiClient, LLMError, LLMErrorType, get_gemini_client
from app.shared.llm.prompts import (
    JD_EXTRACTION_SYSTEM_PROMPT,
    build_jd_extraction_prompt,
)


logger = get_logger(__name__)


@dataclass
class ExtractionResult:
    """Result of an extraction operation."""
    success: bool
    data: Optional[dict[str, Any]] = None
    error_message: Optional[str] = None
    error_type: Optional[str] = None
    tokens_used: int = 0
    retryable: bool = False


class JDExtractor:
    """
    Job Description extraction service.
    
    Extracts structured fields from raw JD text using LLM.
    
    Usage:
        extractor = JDExtractor()
        result = await extractor.extract(raw_jd)
        
        if result.success:
            print(result.data)  # ExtractedFields dict
        else:
            print(result.error_message)
    """
    
    def __init__(
        self,
        client: Optional[GeminiClient] = None,
        temperature: float = 0.0,
        max_tokens: int = 2000,
    ) -> None:
        """
        Initialize JD extractor.
        
        Args:
            client: Gemini client (creates default if None)
            temperature: LLM temperature (0 for deterministic)
            max_tokens: Max output tokens
        """
        self.client = client or get_gemini_client()
        self.temperature = temperature
        self.max_tokens = max_tokens
    
    async def extract(self, raw_jd: str) -> ExtractionResult:
        """
        Extract structured fields from job description.
        
        Args:
            raw_jd: Raw job description text
            
        Returns:
            ExtractionResult with success status and data/error
        """
        if not raw_jd or not raw_jd.strip():
            return ExtractionResult(
                success=False,
                error_message="Empty job description",
                error_type="validation_error",
                retryable=False,
            )
        
        # Truncate very long JDs to avoid token limits
        max_jd_length = 15000  # ~4k tokens
        if len(raw_jd) > max_jd_length:
            logger.warning(f"JD truncated from {len(raw_jd)} to {max_jd_length} chars")
            raw_jd = raw_jd[:max_jd_length] + "\n... [truncated]"
        
        try:
            # Build prompt
            prompt = build_jd_extraction_prompt(raw_jd)
            
            # Call LLM
            response = await self.client.generate(
                prompt=prompt,
                system_instruction=JD_EXTRACTION_SYSTEM_PROMPT,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            
            # Parse JSON response
            data = self.client._parse_json(response.content)
            
            # Validate and clean the extracted data
            cleaned_data = self._clean_extracted_data(data)
            
            logger.info(
                "JD extraction successful",
                extra={
                    "tokens_used": response.total_tokens,
                    "confidence": cleaned_data.get("extraction_confidence"),
                }
            )
            
            return ExtractionResult(
                success=True,
                data=cleaned_data,
                tokens_used=response.total_tokens,
            )
            
        except LLMError as e:
            logger.error(
                f"JD extraction failed: {e}",
                extra={
                    "error_type": e.error_type.value,
                    "retryable": e.retryable,
                }
            )
            return ExtractionResult(
                success=False,
                error_message=str(e.message),
                error_type=e.error_type.value,
                retryable=e.retryable,
            )
        except Exception as e:
            logger.exception(f"Unexpected error in JD extraction: {e}")
            return ExtractionResult(
                success=False,
                error_message=f"Unexpected error: {str(e)}",
                error_type="unknown",
                retryable=True,
            )
    
    def _clean_extracted_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Clean and validate extracted data.
        
        Args:
            data: Raw extracted data from LLM
            
        Returns:
            Cleaned data dict
        """
        cleaned = {}
        
        # String fields
        string_fields = [
            "title", "description", "requirements", "location",
            "city", "state", "country", "work_type", "compensation"
        ]
        for field in string_fields:
            value = data.get(field)
            if value and isinstance(value, str):
                cleaned[field] = value.strip()
            else:
                cleaned[field] = None
        
        # Normalize work_type
        if cleaned.get("work_type"):
            wt = cleaned["work_type"].lower()
            if "remote" in wt:
                cleaned["work_type"] = "remote"
            elif "hybrid" in wt:
                cleaned["work_type"] = "hybrid"
            elif "onsite" in wt or "on-site" in wt or "office" in wt:
                cleaned["work_type"] = "onsite"
            else:
                cleaned["work_type"] = None
        
        # Numeric fields
        for field in ["salary_range_min", "salary_range_max"]:
            value = data.get(field)
            if value is not None:
                try:
                    cleaned[field] = float(value)
                except (ValueError, TypeError):
                    cleaned[field] = None
            else:
                cleaned[field] = None
        
        # Integer fields
        openings = data.get("openings_count")
        if openings is not None:
            try:
                cleaned["openings_count"] = int(openings)
            except (ValueError, TypeError):
                cleaned["openings_count"] = 1
        else:
            cleaned["openings_count"] = 1
        
        # Confidence score (0-1)
        confidence = data.get("extraction_confidence")
        if confidence is not None:
            try:
                conf_value = float(confidence)
                cleaned["extraction_confidence"] = max(0, min(1, conf_value))
            except (ValueError, TypeError):
                cleaned["extraction_confidence"] = None
        else:
            cleaned["extraction_confidence"] = None
        
        # Shift preferences (dict)
        shift_prefs = data.get("shift_preferences")
        if shift_prefs and isinstance(shift_prefs, dict):
            cleaned["shift_preferences"] = shift_prefs
        else:
            cleaned["shift_preferences"] = None
        
        return cleaned


# Global extractor instance
_extractor: Optional[JDExtractor] = None


def get_jd_extractor() -> JDExtractor:
    """Get or create global JD extractor."""
    global _extractor
    if _extractor is None:
        _extractor = JDExtractor()
    return _extractor


async def extract_jd(raw_jd: str) -> ExtractionResult:
    """
    Convenience function for JD extraction.
    
    Args:
        raw_jd: Raw job description text
        
    Returns:
        ExtractionResult
    """
    extractor = get_jd_extractor()
    return await extractor.extract(raw_jd)
