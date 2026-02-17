"""
Seed job from Screening Agent's DB into Aiviue for testing.

Use this when Screening Agent provides job data - we insert it with the same
job_id so they can call our API with their IDs.

Usage:
    From server/ directory:
        python scripts/seed_screening_job.py
        python scripts/seed_screening_job.py --verify

    Or:
        cd server && python scripts/seed_screening_job.py
"""

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from uuid import UUID

# Ensure server root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.constants import JobStatus
from app.domains.employer.models import Employer
from app.domains.job.models import Job
from app.shared.database import async_session_factory


# Job data from Screening Agent (their DB format)
SCREENING_AGENT_JOB = {
    "id": "4523d67f-f899-4ce0-b9d1-69d32a2f097c",
    "title": "Orange Antelopes Personal Assistant position in Bhopal(Madhya Pradesh)",
    "description": "Looking for experienced Meta Ads specialist to manage client campaigns",
    "requirements": "Minimum 2 years experience in Meta Ads, experience with e-commerce campaigns preferred",
    "salary_range_min": 25000.00,
    "salary_range_max": 45000.00,
    "location": "Mumbai, India",
    "shift_preferences": '{"shifts": ["day"], "remote_work": true, "weekend_work": false}',
    "is_active": True,
}

# Employer for screening test jobs (we create if not exists)
# Use a valid email format (.local fails Pydantic/EmailStr validation on login)
SEED_EMPLOYER_EMAIL = "screening-test@orange-antelopes.aiviue.com"
SEED_EMPLOYER_COMPANY = "Orange Antelopes (Screening Test)"


async def get_or_create_employer(session: AsyncSession) -> Employer:
    """Get or create the seed employer for screening test jobs."""
    result = await session.execute(
        select(Employer).where(Employer.email == SEED_EMPLOYER_EMAIL).where(Employer.is_active == True)
    )
    employer = result.scalar_one_or_none()
    if employer:
        return employer

    employer = Employer(
        name="Screening Test Employer",
        email=SEED_EMPLOYER_EMAIL,
        company_name=SEED_EMPLOYER_COMPANY,
        company_description="Placeholder employer for screening agent integration testing",
        is_active=True,
    )
    session.add(employer)
    await session.flush()
    await session.refresh(employer)
    print(f"Created employer: {employer.id} ({employer.company_name})")
    return employer


async def seed_job(session: AsyncSession) -> Job:
    """Insert the screening job. Idempotent - skips if job already exists."""
    job_id = UUID(SCREENING_AGENT_JOB["id"])

    result = await session.execute(select(Job).where(Job.id == job_id))
    existing = result.scalar_one_or_none()
    if existing:
        if existing.status != JobStatus.PUBLISHED:
            existing.status = JobStatus.PUBLISHED
            existing.published_at = existing.published_at or datetime.now(timezone.utc)
            await session.flush()
            await session.refresh(existing)
            print(f"Updated existing job to published: {job_id}")
        else:
            print(f"Job already exists and is published: {job_id}")
        return existing

    employer = await get_or_create_employer(session)

    shift_prefs = None
    if SCREENING_AGENT_JOB.get("shift_preferences"):
        try:
            shift_prefs = json.loads(SCREENING_AGENT_JOB["shift_preferences"])
        except json.JSONDecodeError:
            pass

    job = Job(
        id=job_id,
        employer_id=employer.id,
        title=SCREENING_AGENT_JOB["title"],
        description=SCREENING_AGENT_JOB["description"],
        requirements=SCREENING_AGENT_JOB.get("requirements"),
        location=SCREENING_AGENT_JOB.get("location") or None,
        city=None,
        state=None,
        salary_range_min=SCREENING_AGENT_JOB.get("salary_range_min"),
        salary_range_max=SCREENING_AGENT_JOB.get("salary_range_max"),
        shift_preferences=shift_prefs,
        status=JobStatus.PUBLISHED,
        published_at=datetime.now(timezone.utc),
        is_active=SCREENING_AGENT_JOB.get("is_active", True),
        openings_count=1,
    )
    session.add(job)
    await session.flush()
    await session.refresh(job)
    print(f"Created job: {job.id} - {job.title[:50]}...")
    return job


async def verify_job(session: AsyncSession) -> bool:
    """Check if the seeded job exists and is published."""
    job_id = UUID(SCREENING_AGENT_JOB["id"])
    result = await session.execute(
        select(Job).where(Job.id == job_id).where(Job.is_active == True)
    )
    job = result.scalar_one_or_none()
    if not job:
        print(f"FAIL: Job {job_id} not found or inactive")
        return False
    if job.status != JobStatus.PUBLISHED:
        print(f"FAIL: Job exists but status={job.status} (need 'published')")
        return False
    print(f"OK: Job {job_id} exists, status={job.status}")
    print(f"    Title: {job.title}")
    print(f"    Employer: {job.employer_id}")
    return True


async def main():
    parser = argparse.ArgumentParser(description="Seed Screening Agent job into Aiviue DB")
    parser.add_argument("--verify", action="store_true", help="Only verify job exists and is published")
    args = parser.parse_args()

    async with async_session_factory() as session:
        try:
            if args.verify:
                ok = await verify_job(session)
                await session.commit()
                sys.exit(0 if ok else 1)
            else:
                await seed_job(session)
                await session.commit()
                print("\nVerifying...")
                await verify_job(session)
        except Exception as e:
            await session.rollback()
            print(f"Error: {e}", file=sys.stderr)
            raise


if __name__ == "__main__":
    asyncio.run(main())
