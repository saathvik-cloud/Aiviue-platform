"""
Gemini LLM Client for Aiviue Platform.

Uses the new google-genai SDK (GA 2025) with:
- Retry logic with exponential backoff
- Structured output (JSON) parsing
- Token usage tracking
- Error handling and classification

SDK Docs: https://googleapis.github.io/python-genai/
"""

import asyncio
import json
from typing import Any, Optional, TypeVar, Type
from dataclasses import dataclass
from enum import Enum

from pydantic import BaseModel

from app.config import settings
from app.shared.logging import get_logger
from app.shared.exceptions import InfraError


logger = get_logger(__name__)


# Type for Pydantic models
T = TypeVar("T", bound=BaseModel)


class LLMErrorType(str, Enum):
    """Classification of LLM errors."""
    RATE_LIMITED = "rate_limited"
    INVALID_API_KEY = "invalid_api_key"
    QUOTA_EXCEEDED = "quota_exceeded"
    MODEL_OVERLOADED = "model_overloaded"
    INVALID_REQUEST = "invalid_request"
    CONTENT_FILTERED = "content_filtered"
    PARSE_ERROR = "parse_error"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


@dataclass
class LLMResponse:
    """Response from LLM call."""
    content: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    finish_reason: Optional[str] = None
    
    @property
    def tokens(self) -> int:
        return self.total_tokens


@dataclass  
class LLMError(Exception):
    """Custom exception for LLM errors."""
    error_type: LLMErrorType
    message: str
    retryable: bool = False
    raw_error: Optional[Exception] = None
    
    def __str__(self) -> str:
        return f"[{self.error_type.value}] {self.message}"


class GeminiClient:
    """
    Async Google Gemini API client using google-genai SDK.
    
    Features:
    - Automatic retries with exponential backoff
    - JSON output parsing
    - Pydantic model validation
    - Token tracking
    
    Usage:
        client = GeminiClient()
        
        # Simple text generation
        response = await client.generate("Explain Python decorators")
        print(response.content)
        
        # Structured JSON output
        data = await client.generate_json(
            prompt="Extract: Senior Python Developer, NYC, 150k",
        )
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        max_retries: int = 3,
        base_delay: float = 1.0,
        timeout: float = 60.0,
    ) -> None:
        """
        Initialize Gemini client.
        
        Args:
            api_key: Gemini API key (defaults to settings)
            model: Model name (defaults to settings)
            max_retries: Max retry attempts
            base_delay: Base delay for exponential backoff
            timeout: Request timeout in seconds
        """
        self.api_key = api_key or settings.gemini_api_key
        self.model = model or settings.gemini_model
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.timeout = timeout
        
        self._client = None
        self._initialized = False
    
    def _ensure_client(self) -> None:
        """Lazy initialization of Gemini client."""
        if self._initialized:
            return
        
        try:
            from google import genai
            
            # New google-genai SDK uses Client object
            self._client = genai.Client(api_key=self.api_key)
            self._initialized = True
            
            logger.info(f"Gemini client initialized with model: {self.model}")
            
        except ImportError:
            raise InfraError(
                message="google-genai package not installed. Run: pip install google-genai",
                error_code="LLM_PACKAGE_MISSING",
                context={"package": "google-genai"}
            )
        except Exception as e:
            raise InfraError(
                message=f"Failed to initialize Gemini client: {str(e)}",
                error_code="LLM_INIT_FAILED",
            )
    
    def _classify_error(self, error: Exception) -> LLMError:
        """Classify error type for retry logic."""
        error_str = str(error).lower()
        
        # Check for rate limiting
        if "rate" in error_str or "429" in error_str or "quota" in error_str:
            if "quota" in error_str:
                return LLMError(
                    error_type=LLMErrorType.QUOTA_EXCEEDED,
                    message="API quota exceeded",
                    retryable=False,
                    raw_error=error,
                )
            return LLMError(
                error_type=LLMErrorType.RATE_LIMITED,
                message="Rate limited by API",
                retryable=True,
                raw_error=error,
            )
        
        # Check for auth errors
        if "api_key" in error_str or "401" in error_str or "403" in error_str:
            return LLMError(
                error_type=LLMErrorType.INVALID_API_KEY,
                message="Invalid API key",
                retryable=False,
                raw_error=error,
            )
        
        # Check for overloaded
        if "overloaded" in error_str or "503" in error_str:
            return LLMError(
                error_type=LLMErrorType.MODEL_OVERLOADED,
                message="Model is overloaded",
                retryable=True,
                raw_error=error,
            )
        
        # Check for content filtering
        if "safety" in error_str or "blocked" in error_str:
            return LLMError(
                error_type=LLMErrorType.CONTENT_FILTERED,
                message="Content was filtered by safety settings",
                retryable=False,
                raw_error=error,
            )
        
        # Check for timeout
        if "timeout" in error_str:
            return LLMError(
                error_type=LLMErrorType.TIMEOUT,
                message="Request timed out",
                retryable=True,
                raw_error=error,
            )
        
        # Default to unknown
        return LLMError(
            error_type=LLMErrorType.UNKNOWN,
            message=str(error),
            retryable=True,  # Retry unknown errors once
            raw_error=error,
        )
    
    def _build_contents(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
    ) -> list[dict]:
        """Build contents for the API call."""
        contents = []
        
        # System instruction as first user message with model acknowledgment
        if system_instruction:
            contents.append({
                "role": "user",
                "parts": [{"text": system_instruction}]
            })
            contents.append({
                "role": "model", 
                "parts": [{"text": "Understood. I will follow these instructions."}]
            })
        
        # User prompt
        contents.append({
            "role": "user",
            "parts": [{"text": prompt}]
        })
        
        return contents
    
    async def _execute_with_retry(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Execute generation with retry logic."""
        self._ensure_client()
        
        last_error: Optional[LLMError] = None
        
        for attempt in range(self.max_retries):
            try:
                # Build generation config
                config = {
                    "temperature": temperature,
                }
                if max_tokens:
                    config["max_output_tokens"] = max_tokens
                
                # Build contents
                contents = self._build_contents(prompt, system_instruction)
                
                # Execute with timeout using the new SDK
                # The new SDK uses client.models.generate_content()
                response = await asyncio.wait_for(
                    asyncio.to_thread(
                        self._client.models.generate_content,
                        model=self.model,
                        contents=contents,
                        config=config,
                    ),
                    timeout=self.timeout,
                )
                
                # Extract response text
                # New SDK: response.text or response.candidates[0].content.parts[0].text
                content = ""
                if hasattr(response, "text"):
                    content = response.text
                elif response.candidates:
                    candidate = response.candidates[0]
                    if candidate.content and candidate.content.parts:
                        content = candidate.content.parts[0].text
                
                if not content:
                    raise LLMError(
                        error_type=LLMErrorType.CONTENT_FILTERED,
                        message="No content returned - likely filtered",
                        retryable=False,
                    )
                
                # Get token usage from usage_metadata
                prompt_tokens = 0
                completion_tokens = 0
                
                if hasattr(response, "usage_metadata") and response.usage_metadata:
                    usage = response.usage_metadata
                    prompt_tokens = getattr(usage, "prompt_token_count", 0) or 0
                    completion_tokens = getattr(usage, "candidates_token_count", 0) or 0
                
                # Get finish reason
                finish_reason = None
                if response.candidates:
                    candidate = response.candidates[0]
                    if hasattr(candidate, "finish_reason"):
                        finish_reason = str(candidate.finish_reason)
                
                logger.debug(
                    f"LLM call successful",
                    extra={
                        "model": self.model,
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": completion_tokens,
                        "finish_reason": finish_reason,
                        "attempt": attempt + 1,
                    }
                )
                
                return LLMResponse(
                    content=content,
                    model=self.model,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=prompt_tokens + completion_tokens,
                    finish_reason=finish_reason,
                )
                
            except LLMError:
                raise
            except asyncio.TimeoutError:
                last_error = LLMError(
                    error_type=LLMErrorType.TIMEOUT,
                    message=f"Request timed out after {self.timeout}s",
                    retryable=True,
                )
            except Exception as e:
                last_error = self._classify_error(e)
            
            # Check if retryable
            if last_error and not last_error.retryable:
                raise last_error
            
            # Calculate backoff delay
            delay = self.base_delay * (2 ** attempt)
            logger.warning(
                f"LLM call failed, retrying in {delay}s",
                extra={
                    "attempt": attempt + 1,
                    "max_retries": self.max_retries,
                    "error_type": last_error.error_type.value if last_error else "unknown",
                }
            )
            await asyncio.sleep(delay)
        
        # All retries exhausted
        raise last_error or LLMError(
            error_type=LLMErrorType.UNKNOWN,
            message="All retries exhausted",
            retryable=False,
        )
    
    async def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Generate text response.
        
        Args:
            prompt: User prompt
            system_instruction: System context/instructions
            temperature: Creativity (0.0-1.0)
            max_tokens: Maximum output tokens
            
        Returns:
            LLMResponse with content and usage
        """
        return await self._execute_with_retry(
            prompt=prompt,
            system_instruction=system_instruction,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    
    async def generate_json(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
    ) -> dict[str, Any]:
        """
        Generate and parse JSON response.
        
        Args:
            prompt: User prompt (should ask for JSON)
            system_instruction: System context
            temperature: Creativity (0.0 recommended for JSON)
            max_tokens: Maximum output tokens
            
        Returns:
            Parsed JSON as dict
            
        Raises:
            LLMError: If JSON parsing fails
        """
        response = await self._execute_with_retry(
            prompt=prompt,
            system_instruction=system_instruction,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
        return self._parse_json(response.content)
    
    async def generate_structured(
        self,
        prompt: str,
        schema: Type[T],
        system_instruction: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
    ) -> T:
        """
        Generate and validate against Pydantic schema.
        
        Args:
            prompt: User prompt
            schema: Pydantic model class
            system_instruction: System context
            temperature: Creativity
            max_tokens: Maximum output tokens
            
        Returns:
            Validated Pydantic model instance
            
        Raises:
            LLMError: If parsing or validation fails
        """
        data = await self.generate_json(
            prompt=prompt,
            system_instruction=system_instruction,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
        try:
            return schema.model_validate(data)
        except Exception as e:
            logger.error(f"Schema validation failed: {e}", extra={"data": data})
            raise LLMError(
                error_type=LLMErrorType.PARSE_ERROR,
                message=f"Schema validation failed: {str(e)}",
                retryable=False,
                raw_error=e,
            )
    
    def _parse_json(self, content: str) -> dict[str, Any]:
        """Parse JSON from LLM response, handling markdown code blocks."""
        # Clean up content
        text = content.strip()
        
        # Remove markdown code blocks if present
        if text.startswith("```"):
            lines = text.split("\n")
            # Remove first line (```json or ```)
            lines = lines[1:]
            # Remove last line (```)
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines)
        
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            logger.error(
                f"JSON parse error: {e}",
                extra={"content": content[:500]}
            )
            raise LLMError(
                error_type=LLMErrorType.PARSE_ERROR,
                message=f"Failed to parse JSON: {str(e)}",
                retryable=False,
                raw_error=e,
            )


# Global client instance (lazy initialized)
_client: Optional[GeminiClient] = None


def get_gemini_client() -> GeminiClient:
    """Get or create global Gemini client."""
    global _client
    if _client is None:
        _client = GeminiClient()
    return _client


async def generate_text(
    prompt: str,
    system_instruction: Optional[str] = None,
    temperature: float = 0.1,
) -> str:
    """Convenience function for simple text generation."""
    client = get_gemini_client()
    response = await client.generate(
        prompt=prompt,
        system_instruction=system_instruction,
        temperature=temperature,
    )
    return response.content


async def generate_json(
    prompt: str,
    system_instruction: Optional[str] = None,
) -> dict[str, Any]:
    """Convenience function for JSON generation."""
    client = get_gemini_client()
    return await client.generate_json(
        prompt=prompt,
        system_instruction=system_instruction,
    )
