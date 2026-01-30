"""
LLM Prompts for Aiviue Platform.

Contains structured prompts for various LLM tasks.
"""

from typing import Optional


# ==============================================================================
# JOB DESCRIPTION EXTRACTION PROMPT
# ==============================================================================

JD_EXTRACTION_SYSTEM_PROMPT = """You are an expert job description parser. Your task is to extract structured information from job descriptions accurately and consistently.

## Guidelines

1. **Be precise**: Only extract information explicitly stated. Do not infer or assume.
2. **Handle ambiguity**: If information is unclear or missing, use null.
3. **Normalize data**: 
   - Convert salaries to annual numbers (hourly × 2080, monthly × 12)
   - Normalize work types to: remote, hybrid, or onsite
   - Use proper capitalization for locations
4. **Confidence scoring**: Rate your extraction confidence 0-1 based on clarity of the JD.

## Output Format

Return ONLY valid JSON matching the exact schema. No markdown, no explanation."""


def build_jd_extraction_prompt(raw_jd: str) -> str:
    """
    Build the prompt for JD extraction.
    
    Args:
        raw_jd: Raw job description text
        
    Returns:
        Formatted prompt string
    """
    return f"""Extract structured fields from this job description.

## Job Description
```
{raw_jd}
```

## Required Output Schema (JSON)
{{
    "title": "string or null - the job title",
    "description": "string or null - cleaned job description (remove boilerplate)",
    "requirements": "string or null - skills, qualifications, experience requirements",
    "location": "string or null - full location as stated",
    "city": "string or null - city name",
    "state": "string or null - state/province",
    "country": "string or null - country",
    "work_type": "string or null - one of: remote, hybrid, onsite",
    "salary_range_min": "number or null - minimum annual salary (USD)",
    "salary_range_max": "number or null - maximum annual salary (USD)",
    "compensation": "string or null - full compensation text as stated",
    "shift_preferences": "object or null - shift/schedule info like {{'shifts': ['day', 'night'], 'hours': '9-5'}}",
    "openings_count": "number - count of positions (default 1)",
    "extraction_confidence": "number 0-1 - your confidence in this extraction"
}}

Return ONLY the JSON object, no markdown code blocks."""


# ==============================================================================
# JOB SCREENING CRITERIA EXTRACTION (Future)
# ==============================================================================

SCREENING_CRITERIA_SYSTEM_PROMPT = """You are an expert HR assistant. Extract screening criteria from job descriptions to help evaluate candidates."""


def build_screening_criteria_prompt(
    title: str,
    description: str,
    requirements: Optional[str] = None,
) -> str:
    """
    Build prompt for extracting screening criteria (future use).
    
    Args:
        title: Job title
        description: Job description
        requirements: Requirements text
        
    Returns:
        Formatted prompt string
    """
    req_section = f"\n\n## Requirements\n{requirements}" if requirements else ""
    
    return f"""Extract screening criteria from this job posting.

## Job Title
{title}

## Description
{description}{req_section}

## Required Output Schema (JSON)
{{
    "must_have_skills": ["list of required skills"],
    "nice_to_have_skills": ["list of preferred skills"],
    "min_experience_years": "number or null",
    "education_requirements": ["list of education requirements"],
    "certifications": ["list of required/preferred certs"],
    "screening_questions": [
        {{
            "question": "question text",
            "type": "yes_no | text | number",
            "knockout": true/false
        }}
    ]
}}

Return ONLY the JSON object."""


# ==============================================================================
# RESUME PARSING (Future)
# ==============================================================================

RESUME_PARSE_SYSTEM_PROMPT = """You are an expert resume parser. Extract structured information from resumes accurately."""


def build_resume_parse_prompt(resume_text: str) -> str:
    """
    Build prompt for resume parsing (future use).
    
    Args:
        resume_text: Raw resume text
        
    Returns:
        Formatted prompt string
    """
    return f"""Parse this resume into structured fields.

## Resume
```
{resume_text}
```

## Required Output Schema (JSON)
{{
    "name": "string",
    "email": "string or null",
    "phone": "string or null",
    "location": "string or null",
    "summary": "string or null - professional summary",
    "total_experience_years": "number or null",
    "skills": ["list of skills"],
    "experience": [
        {{
            "title": "job title",
            "company": "company name",
            "start_date": "YYYY-MM or null",
            "end_date": "YYYY-MM or 'Present' or null",
            "description": "brief description"
        }}
    ],
    "education": [
        {{
            "degree": "degree name",
            "field": "field of study",
            "institution": "school name",
            "year": "graduation year or null"
        }}
    ],
    "certifications": ["list of certifications"]
}}

Return ONLY the JSON object."""
