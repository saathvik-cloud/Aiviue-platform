"""
Screening domain service for Aiviue Platform.

Business logic for receiving screened applications from screening agent:
- Upsert candidate by mobile
- Create resume if provided
- Create job application (idempotent)
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.constants import ApplicationSource, JobStatus
from app.domains.candidate.models import ProfileStatus, ResumeSource, ResumeStatus
from app.domains.candidate.repository import CandidateRepository
from app.domains.job.repository import JobRepository
from app.domains.job_application.repository import JobApplicationRepository
from app.domains.screening.models import DeadLetterStatus
from app.domains.screening.repository import ScreeningDeadLetterRepository
from app.domains.screening.schemas import (
    ScreeningApplicationSubmitRequest,
    ScreeningApplicationSubmitResponse,
    ScreeningFailedRequestsResponse,
    ScreeningFailedRequestItem,
)
from app.shared.exceptions import NotFoundError, ValidationError
from app.shared.logging import get_logger


logger = get_logger(__name__)


class ScreeningService:
    """
    Service for screening agent integration.

    Receives screened candidate + application, upserts candidate/resume,
    creates job application. Dead-letters failed payloads.
    """

    def __init__(
        self,
        session: AsyncSession,
        candidate_repo: CandidateRepository,
        job_repo: JobRepository,
        application_repo: JobApplicationRepository,
        dead_letter_repo: ScreeningDeadLetterRepository,
    ) -> None:
        self.session = session
        self.candidate_repo = candidate_repo
        self.job_repo = job_repo
        self.application_repo = application_repo
        self.dead_letter_repo = dead_letter_repo

    async def submit_application(
        self,
        payload: ScreeningApplicationSubmitRequest,
    ) -> ScreeningApplicationSubmitResponse:
        """
        Process screening agent payload: upsert candidate, optional resume,
        create/return job application (idempotent).

        - Job must exist and be published.
        - Candidate identified by phone (mapped to mobile); created or updated.
        - Resume created if resume payload provided (source=pdf_upload).
        - Job application created with source_application=screening_agent.
        """
        job_id = payload.job_id
        job = await self.job_repo.get_by_id(job_id)
        if not job:
            raise NotFoundError(
                message="Job not found",
                error_code="JOB_NOT_FOUND",
                context={"job_id": str(job_id)},
            )
        if job.status != JobStatus.PUBLISHED:
            raise ValidationError(
                message="Can only submit applications to published jobs.",
                error_code="JOB_NOT_PUBLISHED",
                context={"job_id": str(job_id), "status": job.status},
            )

        candidate_dict = payload.candidate.to_candidate_dict()
        mobile = candidate_dict["mobile"]

        candidate = await self.candidate_repo.get_by_mobile(mobile)
        if candidate:
            update_data = {k: v for k, v in candidate_dict.items() if k != "mobile"}
            if update_data:
                updated = await self.candidate_repo.update(
                    candidate.id,
                    update_data,
                    candidate.version,
                )
                if updated:
                    candidate = updated
        else:
            candidate = await self.candidate_repo.create({
                **candidate_dict,
                "profile_status": ProfileStatus.COMPLETE,
            })

        resume_id: Optional[UUID] = None
        if payload.resume:
            resume_dict = payload.resume.to_resume_dict()
            if resume_dict:
                resume_data = payload.resume.resume_data
                resume = await self.candidate_repo.create_resume({
                    "candidate_id": candidate.id,
                    "source": ResumeSource.PDF_UPLOAD,
                    "status": ResumeStatus.COMPLETED,
                    "resume_data": resume_data,
                    **resume_dict,
                })
                resume_id = resume.id

        existing = await self.application_repo.get_by_job_and_candidate(job_id, candidate.id)
        if existing:
            await self.session.commit()
            return ScreeningApplicationSubmitResponse(
                application_id=existing.id,
                candidate_id=candidate.id,
                resume_id=resume_id,
                message="Application already exists (idempotent).",
                already_applied=True,
            )

        app_data: dict = {
            "job_id": job_id,
            "candidate_id": candidate.id,
            "source_application": ApplicationSource.SCREENING_AGENT,
            "resume_id": resume_id,
        }
        if payload.resume:
            app_data["resume_pdf_url"] = payload.resume.file_url
            app_data["resume_snapshot"] = payload.resume.resume_data

        application = await self.application_repo.create(app_data)

        try:
            await self.session.commit()
            await self.session.refresh(application)
        except IntegrityError:
            await self.session.rollback()
            existing = await self.application_repo.get_by_job_and_candidate(job_id, candidate.id)
            if existing:
                return ScreeningApplicationSubmitResponse(
                    application_id=existing.id,
                    candidate_id=candidate.id,
                    resume_id=resume_id,
                    message="Application already exists (idempotent).",
                    already_applied=True,
                )
            raise

        logger.info(
            "Screening application submitted",
            extra={
                "application_id": str(application.id),
                "job_id": str(job_id),
                "candidate_id": str(candidate.id),
            },
        )

        return ScreeningApplicationSubmitResponse(
            application_id=application.id,
            candidate_id=candidate.id,
            resume_id=resume_id,
            message="Application submitted successfully.",
            already_applied=False,
        )

    async def list_failed_requests(
        self,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> ScreeningFailedRequestsResponse:
        """
        List dead-lettered screening payloads for inspection/debugging.
        """
        items, total = await self.dead_letter_repo.list(
            status=status,
            limit=limit,
            offset=offset,
        )
        return ScreeningFailedRequestsResponse(
            items=[ScreeningFailedRequestItem.model_validate(r) for r in items],
            total=total,
        )


def get_screening_service(session: AsyncSession) -> ScreeningService:
    """Factory for ScreeningService with dependencies."""
    return ScreeningService(
        session=session,
        candidate_repo=CandidateRepository(session),
        job_repo=JobRepository(session),
        application_repo=JobApplicationRepository(session),
        dead_letter_repo=ScreeningDeadLetterRepository(session),
    )
