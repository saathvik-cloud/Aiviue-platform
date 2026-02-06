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
    "title": "string (REQUIRED) - the job title. If not explicitly stated, infer from the job content (e.g., 'Plumber', 'Software Engineer', 'Data Analyst'). NEVER return null for title - always infer a reasonable job title from the responsibilities and requirements.",
    "description": "string or null - cleaned job description (remove boilerplate)",
    "requirements": "string or null - skills, qualifications, experience requirements",
    "location": "string or null - full location as stated",
    "city": "string or null - city name",
    "state": "string or null - state/province",
    "country": "string or null - country",
    "work_type": "string or null - one of: remote, hybrid, onsite",
    "salary_range_min": "number or null - minimum annual salary",
    "salary_range_max": "number or null - maximum annual salary",
    "currency": "string or null - salary currency code (e.g., INR, USD). Default to INR if not specified",
    "experience_min": "number or null - minimum years of experience required (e.g., 3, 3.5, 0 for freshers)",
    "experience_max": "number or null - maximum years of experience if a range is specified (e.g., 5 for '3-5 years')",
    "shift_preferences": "object or null - shift/schedule info like {{'shifts': ['day', 'night'], 'hours': '9-5'}}",
    "openings_count": "number - count of positions (default 1)",
    "extraction_confidence": "number 0-1 - your confidence in this extraction"
}}

## Salary Extraction Guidelines (IMPORTANT - Read Carefully!)
- **ALWAYS preserve the original unit (monthly/yearly/hourly) when converting**
- **Ask yourself: Is this salary monthly or yearly? Look for context clues like "per month", "p.m.", "per annum", "p.a.", "CTC", "LPA"**

### Common Indian Salary Formats:
- "18k-20k" or "18,000-20,000" → Usually MONTHLY. Convert: 18000*12=216000, 20000*12=240000
- "18-20k per month" → MONTHLY. Convert: 18000*12=216000, 20000*12=240000
- "2.5 LPA - 3 LPA" → YEARLY (LPA = Lakhs Per Annum). Convert: 250000, 300000
- "25,000-30,000 per month" → MONTHLY. Convert: 300000, 360000
- "Competitive salary" → null, null

### Common US/International Formats:
- "$50,000 - $70,000" → Usually YEARLY (annual salary)
- "$25/hour" → HOURLY. Convert: 25*2080=52000
- "$5000/month" → MONTHLY. Convert: 5000*12=60000

### Rules:
1. If "k" is used (like 18k, 20k) without "LPA", assume MONTHLY in India
2. If "LPA" or "per annum" or "p.a." or "yearly" is mentioned, it's already annual
3. If no unit specified and number is small (< 100), it's likely in thousands (e.g., "18-20" means 18k-20k)
4. If salary seems unrealistically low/high after conversion, reconsider the unit

## Experience Extraction Guidelines (IMPORTANT!)
- **ALWAYS return experience in YEARS (decimal allowed)**
- Look for phrases like "X years experience", "X+ years", "X-Y years", "minimum X years"

### Experience Format Examples:
- "3+ years" → experience_min: 3, experience_max: null
- "3-5 years" → experience_min: 3, experience_max: 5
- "at least 2 years" → experience_min: 2, experience_max: null
- "fresher" or "entry level" → experience_min: 0, experience_max: 1
- "0-5 years" → experience_min: 0, experience_max: 5

### Experience in MONTHS (Convert to Years!):
- "6 months" → experience_min: 0.5, experience_max: null
- "6-12 months" → experience_min: 0.5, experience_max: 1
- "18 months" → experience_min: 1.5, experience_max: null
- "1-2 years or 12-24 months" → experience_min: 1, experience_max: 2

### Rules:
1. Convert months to years: months ÷ 12 (e.g., 6 months = 0.5 years)
2. If no experience mentioned, use null for both
3. For freshers/entry-level with no specific range, use 0-1

## Shift Preferences Guidelines
- Extract shift information as an object with any available details
- Look for: timing, hours, shift type, flexibility

### Shift Format Examples:
- "Day shift" → {{"shift": "day"}}
- "Night shift 10PM-6AM" → {{"shift": "night", "hours": "10PM-6AM"}}
- "8-10 hours per day" → {{"hours": "8-10 hours per day"}}
- "9 AM to 5 PM" or "9-5" → {{"hours": "9AM-5PM"}}
- "Rotational shifts" → {{"shift": "rotational"}}
- "Flexible timing" → {{"shift": "flexible"}}
- "Morning/Evening shifts" → {{"shifts": ["morning", "evening"]}}
- If no shift info mentioned → null

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


# ==============================================================================
# JOB DESCRIPTION GENERATION PROMPT (AIVI Bot)
# ==============================================================================

JD_GENERATION_SYSTEM_PROMPT = """You are an expert HR copywriter specializing in creating compelling, professional job descriptions. Your task is to generate a well-structured job description from structured input data.

## Guidelines

1. **Be professional**: Use clear, professional language appropriate for job postings.
2. **Be engaging**: Write in a way that attracts qualified candidates.
3. **Be accurate**: Only include information provided - never invent or assume details.
4. **Be structured**: Use clear sections with proper formatting.
5. **Be concise**: Keep descriptions focused and readable (300-800 words ideal).

## Output Format

Return ONLY valid JSON with the generated content. No markdown code blocks or explanations."""


def build_jd_generation_prompt(
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
) -> str:
    """
    Build prompt for generating a job description from structured data.
    
    This is called at the end of the AIVI bot conversation flow.
    
    Args:
        title: Job title (required)
        requirements: Skills/qualifications the user mentioned
        city: City name
        state: State/province
        country: Country
        work_type: remote/hybrid/onsite
        salary_min: Minimum salary
        salary_max: Maximum salary
        currency: Currency code (INR, USD, etc.)
        experience_min: Minimum years of experience
        experience_max: Maximum years of experience
        shift_preference: day/night/flexible
        openings_count: Number of positions
        company_name: Company name for personalization
        
    Returns:
        Formatted prompt string
    """
    # Build location string
    location_parts = [p for p in [city, state, country] if p]
    location = ", ".join(location_parts) if location_parts else "Not specified"
    
    # Build salary string
    if salary_min and salary_max:
        salary = f"{currency} {salary_min:,.0f} - {salary_max:,.0f} per annum"
    elif salary_min:
        salary = f"{currency} {salary_min:,.0f}+ per annum"
    elif salary_max:
        salary = f"Up to {currency} {salary_max:,.0f} per annum"
    else:
        salary = "Competitive"
    
    # Build experience string
    if experience_min is not None and experience_max is not None:
        experience = f"{experience_min}-{experience_max} years"
    elif experience_min is not None:
        experience = f"{experience_min}+ years"
    elif experience_max is not None:
        experience = f"Up to {experience_max} years"
    else:
        experience = "Open to all experience levels"
    
    # Normalize work type display
    work_type_display = {
        "remote": "Remote",
        "hybrid": "Hybrid (Remote + Office)",
        "onsite": "On-site",
    }.get(work_type, "Flexible") if work_type else "Flexible"
    
    # Normalize shift display
    shift_display = {
        "day": "Day Shift",
        "night": "Night Shift",
        "flexible": "Flexible Hours",
        "rotational": "Rotational Shifts",
    }.get(shift_preference, shift_preference) if shift_preference else "Standard Business Hours"
    
    company_context = f"for {company_name}" if company_name else ""
    
    return f"""Generate a professional job description {company_context} using the following details.

## Input Data

- **Job Title**: {title}
- **Location**: {location}
- **Work Type**: {work_type_display}
- **Salary Range**: {salary}
- **Experience Required**: {experience}
- **Shift Preference**: {shift_display}
- **Number of Openings**: {openings_count}
- **Requirements/Skills**: {requirements or "Not specified - create general requirements based on the job title"}

## Required Output Schema (JSON)

{{
    "description": "string - A well-written job description (2-4 paragraphs) covering role overview, responsibilities, and what success looks like",
    "requirements": "string - Bullet-pointed list of requirements and qualifications (use newlines and dashes)",
    "summary": "string - A 1-2 sentence summary for job listings"
}}

## Writing Guidelines

1. **Description Section**:
   - Start with an engaging opening about the role
   - Describe key responsibilities (3-5 main duties)
   - Mention growth opportunities if applicable
   - End with a call-to-action to apply

2. **Requirements Section**:
   - List 5-8 key requirements as bullet points
   - Include both technical and soft skills
   - Mention experience requirement
   - Include education if relevant for the role

3. **Summary Section**:
   - Keep it under 150 characters
   - Highlight the most attractive aspect of the role

Return ONLY the JSON object with description, requirements, and summary fields."""
