"""
Job Description Generator for Aiviue Platform.

Generates professional job descriptions from structured data using LLM.
Used at the end of the AIVI bot conversation flow.
"""

import json
from dataclasses import dataclass
from typing import Optional

from app.shared.llm.client import get_gemini_client, GeminiClient
from app.shared.llm.prompts import JD_GENERATION_SYSTEM_PROMPT, build_jd_generation_prompt
from app.shared.logging import get_logger


logger = get_logger(__name__)


@dataclass
class GeneratedJobContent:
    """Result of job description generation."""
    description: str
    requirements: str
    summary: str
    success: bool = True
    error: Optional[str] = None


# Fallback templates when LLM fails
FALLBACK_DESCRIPTION_TEMPLATE = """We are looking for a talented {title} to join our team{location_text}.

As a {title}, you will play a key role in our organization{work_type_text}. This is an excellent opportunity for someone with {experience_text} of experience who is looking to make an impact.

We offer {salary_text} along with a comprehensive benefits package. If you're passionate about this field and ready for your next challenge, we'd love to hear from you!"""

FALLBACK_REQUIREMENTS_TEMPLATE = """- {experience_text} of relevant experience
- Strong communication and collaboration skills
- Problem-solving abilities and attention to detail
- Ability to work {work_type_text}
- Self-motivated and able to work independently"""


class JDGenerator:
    """
    Generates job descriptions from structured data.
    
    Uses LLM (Gemini) with guardrails:
    - Input validation
    - Strict output schema
    - Retry with exponential backoff
    - Fallback templates on failure
    """
    
    def __init__(self, client: Optional[GeminiClient] = None):
        """Initialize generator with optional LLM client."""
        self._client = client
    
    @property
    def client(self) -> GeminiClient:
        """Get or create LLM client."""
        if self._client is None:
            self._client = get_gemini_client()
        return self._client
    
    async def generate(
        self,
        title: str,
        requirements: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        country: Optional[str] = None,
        work_type: Optional[str] = None,
        salary_min: Optional[float] = None,
        salary_max: Optional[float] = None,
        currency: str = "INR",
        experience_min: Optional[float] = None,
        experience_max: Optional[float] = None,
        shift_preference: Optional[str] = None,
        openings_count: int = 1,
        company_name: Optional[str] = None,
    ) -> GeneratedJobContent:
        """
        Generate a job description from structured data.
        
        Args:
            title: Job title (required)
            requirements: Skills/qualifications mentioned by user
            city: City name
            state: State/province
            country: Country
            work_type: remote/hybrid/onsite
            salary_min: Minimum salary
            salary_max: Maximum salary
            currency: Currency code
            experience_min: Min years experience
            experience_max: Max years experience
            shift_preference: day/night/flexible
            openings_count: Number of positions
            company_name: Company name
            
        Returns:
            GeneratedJobContent with description, requirements, summary
        """
        # Validate required input
        if not title or not title.strip():
            logger.warning("JD generation called without title")
            return self._generate_fallback(
                title="Position",
                work_type=work_type,
                salary_min=salary_min,
                salary_max=salary_max,
                currency=currency,
                experience_min=experience_min,
                experience_max=experience_max,
                city=city,
                error="Title is required",
            )
        
        # Build prompt
        prompt = build_jd_generation_prompt(
            title=title,
            requirements=requirements,
            city=city,
            state=state,
            country=country,
            work_type=work_type,
            salary_min=salary_min,
            salary_max=salary_max,
            currency=currency,
            experience_min=experience_min,
            experience_max=experience_max,
            shift_preference=shift_preference,
            openings_count=openings_count,
            company_name=company_name,
        )
        
        # Try LLM generation with retries
        max_retries = 3
        last_error = None
        
        for attempt in range(max_retries):
            try:
                logger.info(
                    f"Generating JD (attempt {attempt + 1}/{max_retries})",
                    extra={"title": title},
                )
                
                response = await self.client.generate(
                    prompt=prompt,
                    system_prompt=JD_GENERATION_SYSTEM_PROMPT,
                    temperature=0.7,  # Some creativity for engaging content
                    max_tokens=2000,
                )
                
                # Parse and validate response
                result = self._parse_response(response)
                if result:
                    logger.info("JD generated successfully", extra={"title": title})
                    return result
                
                last_error = "Invalid response format"
                
            except Exception as e:
                last_error = str(e)
                logger.warning(
                    f"JD generation attempt {attempt + 1} failed: {e}",
                    extra={"title": title},
                )
                
                # Exponential backoff
                if attempt < max_retries - 1:
                    import asyncio
                    await asyncio.sleep(2 ** attempt)
        
        # All retries failed - use fallback
        logger.error(
            f"JD generation failed after {max_retries} attempts, using fallback",
            extra={"title": title, "error": last_error},
        )
        
        return self._generate_fallback(
            title=title,
            work_type=work_type,
            salary_min=salary_min,
            salary_max=salary_max,
            currency=currency,
            experience_min=experience_min,
            experience_max=experience_max,
            city=city,
            error=last_error,
        )
    
    def _parse_response(self, response: str) -> Optional[GeneratedJobContent]:
        """
        Parse and validate LLM response.
        
        Args:
            response: Raw LLM response string
            
        Returns:
            GeneratedJobContent if valid, None otherwise
        """
        try:
            # Clean response (remove markdown code blocks if present)
            text = response.strip()
            if text.startswith("```"):
                # Remove ```json and closing ```
                lines = text.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                text = "\n".join(lines)
            
            # Parse JSON
            data = json.loads(text)
            
            # Validate required fields
            description = data.get("description", "").strip()
            requirements = data.get("requirements", "").strip()
            summary = data.get("summary", "").strip()
            
            if not description or len(description) < 100:
                logger.warning("Generated description too short")
                return None
            
            if not requirements or len(requirements) < 50:
                logger.warning("Generated requirements too short")
                return None
            
            # Generate summary if missing
            if not summary:
                summary = description[:150].rsplit(" ", 1)[0] + "..."
            
            return GeneratedJobContent(
                description=description,
                requirements=requirements,
                summary=summary,
                success=True,
            )
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM response as JSON: {e}")
            return None
        except Exception as e:
            logger.warning(f"Error parsing LLM response: {e}")
            return None
    
    def _generate_fallback(
        self,
        title: str,
        work_type: Optional[str] = None,
        salary_min: Optional[float] = None,
        salary_max: Optional[float] = None,
        currency: str = "INR",
        experience_min: Optional[float] = None,
        experience_max: Optional[float] = None,
        city: Optional[str] = None,
        error: Optional[str] = None,
    ) -> GeneratedJobContent:
        """
        Generate fallback content when LLM fails.
        
        Args:
            title: Job title
            work_type: Work type
            salary_min: Min salary
            salary_max: Max salary
            currency: Currency
            experience_min: Min experience
            experience_max: Max experience
            city: City
            error: Error message
            
        Returns:
            GeneratedJobContent with fallback content
        """
        # Build text snippets
        location_text = f" in {city}" if city else ""
        
        work_type_map = {
            "remote": " in a fully remote capacity",
            "hybrid": " in a hybrid work arrangement",
            "onsite": " from our office",
        }
        work_type_text = work_type_map.get(work_type, "")
        
        if experience_min and experience_max:
            experience_text = f"{experience_min}-{experience_max} years"
        elif experience_min:
            experience_text = f"{experience_min}+ years"
        else:
            experience_text = "relevant"
        
        if salary_min and salary_max:
            salary_text = f"competitive compensation ({currency} {salary_min:,.0f} - {salary_max:,.0f})"
        elif salary_min:
            salary_text = f"competitive compensation (starting at {currency} {salary_min:,.0f})"
        else:
            salary_text = "competitive compensation"
        
        description = FALLBACK_DESCRIPTION_TEMPLATE.format(
            title=title,
            location_text=location_text,
            work_type_text=work_type_text,
            experience_text=experience_text,
            salary_text=salary_text,
        )
        
        requirements = FALLBACK_REQUIREMENTS_TEMPLATE.format(
            experience_text=experience_text,
            work_type_text=work_type if work_type else "in a team environment",
        )
        
        summary = f"Join our team as a {title}{location_text}. {experience_text} experience required."
        
        return GeneratedJobContent(
            description=description,
            requirements=requirements,
            summary=summary,
            success=False,
            error=error,
        )


# Global generator instance
_generator: Optional[JDGenerator] = None


def get_jd_generator() -> JDGenerator:
    """Get or create global JD generator."""
    global _generator
    if _generator is None:
        _generator = JDGenerator()
    return _generator


async def generate_job_description(
    title: str,
    requirements: Optional[str] = None,
    city: Optional[str] = None,
    state: Optional[str] = None,
    country: Optional[str] = None,
    work_type: Optional[str] = None,
    salary_min: Optional[float] = None,
    salary_max: Optional[float] = None,
    currency: str = "INR",
    experience_min: Optional[float] = None,
    experience_max: Optional[float] = None,
    shift_preference: Optional[str] = None,
    openings_count: int = 1,
    company_name: Optional[str] = None,
) -> GeneratedJobContent:
    """
    Convenience function for job description generation.
    
    Args:
        title: Job title (required)
        ... (see JDGenerator.generate for all args)
        
    Returns:
        GeneratedJobContent
    """
    generator = get_jd_generator()
    return await generator.generate(
        title=title,
        requirements=requirements,
        city=city,
        state=state,
        country=country,
        work_type=work_type,
        salary_min=salary_min,
        salary_max=salary_max,
        currency=currency,
        experience_min=experience_min,
        experience_max=experience_max,
        shift_preference=shift_preference,
        openings_count=openings_count,
        company_name=company_name,
    )
