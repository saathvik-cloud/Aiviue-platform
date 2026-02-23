"""
Interview scheduling background jobs.

- Offer expiry: release slots and cancel schedule when candidate doesn't respond in time.
- Employer confirm timeout: release slot and cancel when employer doesn't confirm within 24h.
- Calendar poll: detect Google Calendar event cancelled externally, mark schedule cancelled.

Jobs run in a loop (interval from constants); optional PostgreSQL advisory lock for single-worker.
"""

from app.domains.interview_scheduling.jobs.runner import run_all_interview_scheduling_jobs

__all__ = ["run_all_interview_scheduling_jobs"]
