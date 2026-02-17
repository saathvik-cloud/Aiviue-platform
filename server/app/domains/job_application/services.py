"""
Job Application Service for Aiviue Platform.

Business logic for apply (idempotent), list applications (employer), and application detail.
Handles ownership (job belongs to employer), published-only, and deduplication.
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.constants import ApplicationSource, JobStatus
from app.domains.candidate.repository import CandidateRepository
from app.domains.candidate.services import build_candidate_response_for_display
from app.domains.job.repository import JobRepository
from app.domains.job_application.repository import JobApplicationRepository
from app.domains.candidate.schemas import AppliedJobIdsResponse
from app.domains.job.schemas import JobListResponse, JobSummaryResponse
from app.domains.job_application.schemas import (
    ApplicationDetailResponse,
    ApplicationListItemResponse,
    ApplicationListResponse,
    JobApplyResponse,
)
from app.shared.exceptions import BusinessError, ForbiddenError, NotFoundError, ValidationError
from app.shared.logging import get_logger
from app.shared.utils.pagination import encode_cursor


logger = get_logger(__name__)


# ==================== SERVICE ====================


class JobApplicationService:
    """
    Service for job application business logic.

    Apply (candidate, idempotent), list applications (employer), get detail (employer).
    """

    def __init__(
        self,
        session: AsyncSession,
        application_repo: JobApplicationRepository,
        job_repo: JobRepository,
        candidate_repo: CandidateRepository,
    ) -> None:
        self.session = session
        self.app_repo = application_repo
        self.job_repo = job_repo
        self.candidate_repo = candidate_repo

    # ==================== APPLY (Candidate) ====================

    async def get_applied_job_ids(self, candidate_id: UUID) -> AppliedJobIdsResponse:
        """
        Get job IDs the candidate has applied to.
        Used by frontend to show Apply vs Applied per job per candidate.
        """
        job_ids = await self.app_repo.list_job_ids_by_candidate_id(candidate_id)
        return AppliedJobIdsResponse(job_ids=job_ids)

    async def list_applied_jobs_paginated(
        self,
        candidate_id: UUID,
        cursor: Optional[str],
        limit: int,
    ) -> JobListResponse:
        """
        List jobs the candidate has applied to, most recent first, cursor-paginated.
        Only returns jobs for this candidate (candidate_id from auth). Same shape as job list.
        """
        applications = await self.app_repo.list_by_candidate_paginated(
            candidate_id=candidate_id,
            cursor=cursor,
            limit=limit,
        )
        has_more = len(applications) > limit
        if has_more:
            applications = applications[:limit]
        items = [
            self._job_to_summary(app.job)
            for app in applications
            if app.job is not None
        ]
        next_cursor = None
        if has_more and applications:
            last = applications[-1]
            next_cursor = encode_cursor(id=last.id, created_at=last.applied_at)
        return JobListResponse(
            items=items,
            next_cursor=next_cursor,
            has_more=has_more,
            total_count=None,
        )

    @staticmethod
    def _job_to_summary(job) -> JobSummaryResponse:
        """Build job summary from Job model (job.employer must be loaded)."""
        employer_name = job.employer.company_name if job.employer else None
        return JobSummaryResponse(
            id=job.id,
            employer_id=job.employer_id,
            employer_name=employer_name,
            title=job.title,
            location=job.location,
            work_type=job.work_type,
            salary_range=job.salary_range,
            currency=job.currency,
            status=job.status,
            openings_count=job.openings_count,
            created_at=job.created_at,
        )

    async def apply(
        self,
        job_id: UUID,
        candidate_id: UUID,
        resume_id: Optional[UUID] = None,
    ) -> JobApplyResponse:
        """
        Candidate applies to a job. Idempotent: if already applied, returns existing.

        - Job must be published.
        - Uses latest completed resume if resume_id not provided.
        - Does not expose source_application.
        """
        # 1. Idempotent: already applied?
        existing = await self.app_repo.get_by_job_and_candidate(job_id, candidate_id)
        if existing:
            return JobApplyResponse(
                application_id=existing.id,
                applied_at=existing.applied_at,
                already_applied=True,
                message="You have already applied to this job.",
            )

        # 2. Job exists and is published
        job = await self.job_repo.get_by_id(job_id)
        if not job:
            raise NotFoundError(
                message="Job not found",
                error_code="JOB_NOT_FOUND",
                context={"job_id": str(job_id)},
            )
        if job.status != JobStatus.PUBLISHED:
            raise BusinessError(
                message="You can only apply to published jobs.",
                error_code="JOB_NOT_PUBLISHED",
                context={"job_id": str(job_id), "status": job.status},
            )

        # 3. Candidate exists
        candidate = await self.candidate_repo.get_by_id(candidate_id)
        if not candidate:
            raise NotFoundError(
                message="Candidate not found",
                error_code="CANDIDATE_NOT_FOUND",
                context={"candidate_id": str(candidate_id)},
            )

        # 4. Resolve resume: optional resume_id or latest completed
        resolved_resume_id: Optional[UUID] = None
        if resume_id is not None:
            resume = await self.candidate_repo.get_resume_by_id(resume_id)
            if not resume or resume.candidate_id != candidate_id:
                raise ValidationError(
                    message="Resume not found or does not belong to you.",
                    error_code="RESUME_NOT_FOUND",
                    context={"resume_id": str(resume_id)},
                )
            # Allow any resume when user explicitly selects it (completed or in-progress)
            resolved_resume_id = resume.id
        else:
            latest = await self.candidate_repo.get_latest_resume(candidate_id)
            if not latest:
                raise BusinessError(
                    message="You need at least one completed resume to apply.",
                    error_code="NO_RESUME",
                    context={"candidate_id": str(candidate_id)},
                )
            resolved_resume_id = latest.id

        # 5. Create application (single insert; unique constraint prevents race duplicate)
        application = await self.app_repo.create({
            "job_id": job_id,
            "candidate_id": candidate_id,
            "applied_at": datetime.now(timezone.utc),
            "source_application": ApplicationSource.PLATFORM,
            "resume_id": resolved_resume_id,
        })
        try:
            await self.session.commit()
            await self.session.refresh(application)
        except IntegrityError:
            await self.session.rollback()
            # Race: another request created the application; return existing (idempotent)
            existing = await self.app_repo.get_by_job_and_candidate(job_id, candidate_id)
            if existing:
                return JobApplyResponse(
                    application_id=existing.id,
                    applied_at=existing.applied_at,
                    already_applied=True,
                    message="You have already applied to this job.",
                )
            raise

        logger.info(
            "Candidate applied to job",
            extra={
                "application_id": str(application.id),
                "job_id": str(job_id),
                "candidate_id": str(candidate_id),
            },
        )

        return JobApplyResponse(
            application_id=application.id,
            applied_at=application.applied_at,
            already_applied=False,
            message="Application submitted successfully.",
        )

    # ==================== LIST APPLICATIONS (Employer) ====================

    async def list_applications_for_job(
        self,
        job_id: UUID,
        employer_id: UUID,
    ) -> ApplicationListResponse:
        """
        List applications for a job. Only for job owner and published jobs.
        Does not expose source_application.
        """
        job = await self.job_repo.get_by_id_with_role(job_id)
        if not job:
            raise NotFoundError(
                message="Job not found",
                error_code="JOB_NOT_FOUND",
                context={"job_id": str(job_id)},
            )
        if job.employer_id != employer_id:
            raise ForbiddenError(
                message="You can only view applications for your own jobs.",
                error_code="FORBIDDEN",
                context={"job_id": str(job_id)},
            )
        if job.status != JobStatus.PUBLISHED:
            raise BusinessError(
                message="Applications are only listed for published jobs.",
                error_code="JOB_NOT_PUBLISHED",
                context={"job_id": str(job_id)},
            )

        applications = await self.app_repo.list_by_job_id(job_id)
        role_name = job.role.name if job.role else None

        items = [
            ApplicationListItemResponse(
                id=app.id,
                job_id=app.job_id,
                candidate_id=app.candidate_id,
                applied_at=app.applied_at,
                candidate_name=app.candidate.name if app.candidate else "",
                job_title=job.title,
                role_name=role_name,
                resume_id=app.resume_id,
                has_resume_pdf=bool(app.resume_id or app.resume_pdf_url or app.resume_snapshot),
            )
            for app in applications
        ]

        return ApplicationListResponse(
            job_id=job_id,
            job_title=job.title,
            items=items,
        )

    # ==================== APPLICATION DETAIL (Employer) ====================

    async def get_application_detail(
        self,
        application_id: UUID,
        job_id: UUID,
        employer_id: UUID,
    ) -> ApplicationDetailResponse:
        """
        Get full application detail: candidate profile + resume for display/download.
        Only for job owner; job must be published. Does not expose source_application.
        """
        job = await self.job_repo.get_by_id_with_role(job_id)
        if not job:
            raise NotFoundError(
                message="Job not found",
                error_code="JOB_NOT_FOUND",
                context={"job_id": str(job_id)},
            )
        if job.employer_id != employer_id:
            raise ForbiddenError(
                message="You can only view applications for your own jobs.",
                error_code="FORBIDDEN",
                context={"job_id": str(job_id)},
            )
        if job.status != JobStatus.PUBLISHED:
            raise BusinessError(
                message="Applications are only visible for published jobs.",
                error_code="JOB_NOT_PUBLISHED",
                context={"job_id": str(job_id)},
            )

        application = await self.app_repo.get_by_id_with_candidate_and_resume(
            application_id,
            job_id,
        )
        if not application:
            raise NotFoundError(
                message="Application not found",
                error_code="APPLICATION_NOT_FOUND",
                context={"application_id": str(application_id), "job_id": str(job_id)},
            )

        candidate = application.candidate
        if not candidate:
            raise NotFoundError(
                message="Candidate not found for this application.",
                error_code="CANDIDATE_NOT_FOUND",
                context={"application_id": str(application_id)},
            )

        # Build candidate response with masked Aadhaar/PAN and resume stats
        count, latest_ver = await self.candidate_repo.get_resume_stats(candidate.id)
        candidate_response = build_candidate_response_for_display(
            candidate,
            has_resume=count > 0,
            latest_resume_version=latest_ver,
        )

        resume_response = None
        if application.resume:
            from app.domains.candidate.schemas import CandidateResumeResponse
            resume_response = CandidateResumeResponse.model_validate(application.resume)

        return ApplicationDetailResponse(
            id=application.id,
            job_id=application.job_id,
            candidate_id=application.candidate_id,
            applied_at=application.applied_at,
            candidate=candidate_response,
            resume=resume_response,
            resume_pdf_url=application.resume_pdf_url,
            resume_snapshot=application.resume_snapshot,
        )


# ==================== FACTORY ====================


def get_job_application_service(session: AsyncSession) -> JobApplicationService:
    """Factory for JobApplicationService with dependencies."""
    return JobApplicationService(
        session=session,
        application_repo=JobApplicationRepository(session),
        job_repo=JobRepository(session),
        candidate_repo=CandidateRepository(session),
    )
