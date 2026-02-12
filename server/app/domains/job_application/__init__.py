"""
Job Application domain for Aiviue Platform.

Links candidates to jobs (apply flow). Used by:
- Application Management (employer views applications per job)
- Candidate apply (platform); future: screening agent ingestion.
"""

from app.domains.job_application.models import JobApplication

__all__ = ["JobApplication"]
