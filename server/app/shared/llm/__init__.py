"""
LLM Module for Aiviue Platform.

Provides async Gemini client with retry logic and structured output.

Usage:
    # Simple text generation
    from app.shared.llm import generate_text, generate_json
    
    text = await generate_text("Explain Python decorators")
    data = await generate_json("Extract: ...")
    
    # JD Extraction
    from app.shared.llm import extract_jd, JDExtractor
    
    result = await extract_jd(raw_jd)
    if result.success:
        print(result.data)
    
    # Full client control
    from app.shared.llm import GeminiClient
    
    client = GeminiClient()
    response = await client.generate_structured(prompt, MySchema)
"""

from app.shared.llm.client import (
    GeminiClient,
    LLMResponse,
    LLMError,
    LLMErrorType,
    get_gemini_client,
    generate_text,
    generate_json,
)
from app.shared.llm.prompts import (
    JD_EXTRACTION_SYSTEM_PROMPT,
    build_jd_extraction_prompt,
    build_screening_criteria_prompt,
    build_resume_parse_prompt,
)
from app.shared.llm.extraction import (
    JDExtractor,
    ExtractionResult,
    get_jd_extractor,
    extract_jd,
)

__all__ = [
    # Client
    "GeminiClient",
    "LLMResponse",
    "LLMError",
    "LLMErrorType",
    "get_gemini_client",
    "generate_text",
    "generate_json",
    # Prompts
    "JD_EXTRACTION_SYSTEM_PROMPT",
    "build_jd_extraction_prompt",
    "build_screening_criteria_prompt",
    "build_resume_parse_prompt",
    # Extraction
    "JDExtractor",
    "ExtractionResult",
    "get_jd_extractor",
    "extract_jd",
]
