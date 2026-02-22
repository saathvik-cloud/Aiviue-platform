"""
Interview scheduling API routes.

Employer: availability, slots, send offer, confirm, cancel.
Candidate: view slots, pick slot, cancel.
"""

from app.domains.interview_scheduling.api.routes import router

__all__ = ["router"]
