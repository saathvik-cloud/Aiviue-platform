"""
Test Data Constants for AIVIUE Backend Tests

This file contains all dummy data, constants, and sample payloads
used across all test modules.

Usage:
    from tests.test_data import SAMPLE_EMPLOYER, SAMPLE_JOB, SAMPLE_JD
"""

import uuid
from datetime import datetime, timezone


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def generate_unique_email(prefix: str = "test") -> str:
    """Generate a unique test email to avoid conflicts."""
    return f"{prefix}_{uuid.uuid4().hex[:8]}@pytest.com"


def generate_unique_phone() -> str:
    """Generate a unique test phone number to avoid conflicts."""
    import random
    # Generate random 10-digit number (only digits, no hex)
    area_code = random.randint(200, 999)
    prefix = random.randint(200, 999)
    line = random.randint(1000, 9999)
    return f"+1-{area_code}-{prefix}-{line}"


def generate_uuid() -> str:
    """Generate a new UUID string."""
    return str(uuid.uuid4())


def generate_unique_indian_mobile() -> str:
    """Generate unique 10-digit Indian mobile for screening tests."""
    import random
    return str(random.randint(9000000000, 9999999999))


# =============================================================================
# EMPLOYER TEST DATA
# =============================================================================

SAMPLE_EMPLOYER = {
    "name": "John Doe",
    "email": "john.doe@acmecorp.com",
    "phone": "+1-234-567-8900",  # With country code and formatting
    "company_name": "Acme Corporation",
    "company_description": "We build amazing products that solve real problems.",
    "company_website": "https://acmecorp.com",
    "company_size": "medium",  # Valid values: startup, small, medium, large, enterprise
    "industry": "Technology",
    "headquarters_location": "New York, NY",
    "city": "New York",
    "state": "NY",
    "country": "USA",
}

SAMPLE_EMPLOYER_MINIMAL = {
    "name": "Jane Smith",
    "email": "jane.smith@startup.io",
    "company_name": "Tech Startup Inc",
}

SAMPLE_EMPLOYER_UPDATE = {
    "name": "John Doe Updated",
    # Note: Don't include phone here - use generate_unique_phone() in tests if updating phone
    "company_description": "Updated description - Now we build even better products!",
    "company_size": "large",  # Valid values: startup, small, medium, large, enterprise
}

INVALID_EMPLOYER_PAYLOADS = [
    # Missing required fields
    {"name": "Only Name"},
    {"email": "only@email.com"},
    {"company_name": "Only Company"},
    # Invalid email
    {"name": "Test", "email": "invalid-email", "company_name": "Test Co"},
    # Empty strings
    {"name": "", "email": "test@test.com", "company_name": "Test Co"},
    {"name": "Test", "email": "test@test.com", "company_name": ""},
]


# =============================================================================
# JOB TEST DATA
# =============================================================================

SAMPLE_JOB = {
    "title": "Senior Python Developer",
    "description": """
    We are looking for a Senior Python Developer to join our growing team.
    
    You will be responsible for:
    - Building scalable backend services
    - Working with FastAPI and PostgreSQL
    - Collaborating with frontend team
    - Mentoring junior developers
    
    This is a remote-friendly position with competitive compensation.
    """,
    "requirements": """
    - 5+ years of Python experience
    - Experience with FastAPI or Django
    - Strong SQL and database design skills
    - AWS/GCP cloud experience
    - Excellent communication skills
    """,
    "location": "New York, NY",
    "city": "New York",
    "state": "NY",
    "country": "USA",
    "work_type": "remote",
    "salary_range_min": 150000,
    "salary_range_max": 180000,
    "compensation": "$150,000 - $180,000 per year + equity",
    "openings_count": 2,
}

SAMPLE_JOB_MINIMAL = {
    "title": "Product Manager",
    "description": "Looking for an experienced PM to lead our product team.",
}

SAMPLE_JOB_UPDATE = {
    "title": "Lead Python Developer",
    "salary_range_min": 160000,
    "salary_range_max": 200000,
    "openings_count": 3,
}

JOB_STATUSES = ["draft", "published", "paused", "closed"]

WORK_TYPES = ["remote", "hybrid", "onsite"]

INVALID_JOB_PAYLOADS = [
    # Missing required fields
    {"title": "Only Title"},
    {"description": "Only description"},
    # Invalid work type
    {"title": "Test", "description": "Test desc", "work_type": "invalid_type"},
    # Invalid salary (min > max)
    {"title": "Test", "description": "Test", "salary_range_min": 200000, "salary_range_max": 100000},
    # Empty strings
    {"title": "", "description": "Test"},
    {"title": "Test", "description": ""},
]


# =============================================================================
# JD EXTRACTION TEST DATA
# =============================================================================

SAMPLE_JD_RAW = """
Senior Software Engineer - Remote

About Us:
TechCorp is a fast-growing startup building the future of AI-powered automation.

Location: San Francisco, CA (Remote OK)

Salary: $140,000 - $180,000 annually

What You'll Do:
- Design and build scalable microservices
- Work with Python, FastAPI, and PostgreSQL
- Collaborate with ML engineers on AI features
- Participate in code reviews and architectural decisions

Requirements:
- 5+ years of backend development experience
- Strong Python skills (FastAPI, Django, or Flask)
- Experience with SQL databases and Redis
- Knowledge of Docker and Kubernetes
- Excellent problem-solving skills

Benefits:
- Competitive salary + equity
- Health, dental, and vision insurance
- Unlimited PTO
- Remote-first culture

To apply, send your resume to jobs@techcorp.io
"""

SAMPLE_JD_MINIMAL = """
We're hiring a Python Developer.
Remote position.
$100k-$150k salary.
"""

SAMPLE_JD_COMPLEX = """
🚀 SENIOR FULL-STACK ENGINEER 🚀

📍 Location: New York City (Hybrid - 2 days in office)
💰 Compensation: $160,000 - $200,000 + 0.5% equity

About the Role:
We're looking for a Senior Full-Stack Engineer to join our core product team.
You'll work on our flagship SaaS platform used by Fortune 500 companies.

Tech Stack:
- Backend: Python (FastAPI), Node.js
- Frontend: React, TypeScript, Next.js
- Database: PostgreSQL, Redis, MongoDB
- Infrastructure: AWS, Docker, Kubernetes

Requirements:
✅ 6+ years of software engineering experience
✅ Strong experience with Python AND JavaScript/TypeScript
✅ Experience building and scaling SaaS products
✅ Familiarity with CI/CD pipelines
✅ BS/MS in Computer Science or equivalent

Nice to Have:
- Experience with AI/ML integration
- Startup experience
- Open source contributions

We're hiring for 3 positions.

Apply now at: https://careers.example.com/senior-engineer
"""

EXPECTED_EXTRACTION_FIELDS = [
    "title",
    "description",
    "requirements",
    "location",
    "city",
    "state",
    "country",
    "work_type",
    "salary_range_min",
    "salary_range_max",
    "compensation",
    "openings_count",
    "extraction_confidence",
]


# =============================================================================
# SCREENING API TEST DATA
# =============================================================================

def screening_payload_minimal(job_id: str, phone: str = None) -> dict:
    """Minimal screening payload (candidate only, no resume)."""
    import random
    phone = phone or str(random.randint(9000000000, 9999999999))
    return {
        "job_id": job_id,
        "candidate": {
            "phone": phone,
            "name": "Screening Test Candidate",
        },
    }


def screening_payload_full(job_id: str, phone: str = None) -> dict:
    """Full screening payload with candidate + resume."""
    import random
    phone = phone or str(random.randint(9000000000, 9999999999))
    return {
        "job_id": job_id,
        "correlation_id": f"test-{uuid.uuid4().hex[:8]}",
        "candidate": {
            "phone": phone,
            "name": "Screening Full Candidate",
            "email": "screening@test.com",
            "current_location": "Mumbai, Maharashtra",
            "years_experience": 3,
            "relevant_skills": "Python, SQL",
            "job_title": "Data Engineer",
            "work_preference": "remote",
            "is_fresher": False,
            "resume_summary": "LLM summary",
            "fit_score_details": {"overall": 78},
        },
        "resume": {
            "file_url": "https://storage.example.com/resume.pdf",
            "file_type": "pdf",
            "file_name": "resume.pdf",
            "file_size": 102400,
            "mime_type": "application/pdf",
            "resume_data": {"sections": {"summary": "Test resume"}},
        },
    }


# =============================================================================
# API RESPONSE EXPECTATIONS
# =============================================================================

EMPLOYER_RESPONSE_FIELDS = [
    "id",
    "name",
    "email",
    "company_name",
    "created_at",
    "updated_at",
    "is_active",
    "version",
]

JOB_RESPONSE_FIELDS = [
    "id",
    "employer_id",
    "title",
    "description",
    "status",
    "created_at",
    "updated_at",
    "is_active",
    "version",
]

EXTRACTION_RESPONSE_FIELDS = [
    "id",
    "status",
    "raw_jd_length",
]


# =============================================================================
# ERROR CODES
# =============================================================================

ERROR_CODES = {
    "EMPLOYER_NOT_FOUND": "EMPLOYER_NOT_FOUND",
    "DUPLICATE_EMAIL": "DUPLICATE_EMAIL",
    "JOB_NOT_FOUND": "JOB_NOT_FOUND",
    "INVALID_JOB_STATUS": "INVALID_JOB_STATUS",
    "VERSION_CONFLICT": "VERSION_CONFLICT",
    "VALIDATION_ERROR": "VALIDATION_ERROR",
}


# =============================================================================
# TEST CONFIGURATION
# =============================================================================

TEST_CONFIG = {
    "base_url": "http://localhost:8000",
    "api_prefix": "/api/v1",
    "timeout_seconds": 30,
    "poll_interval_seconds": 1,
    "max_poll_attempts": 30,
}
