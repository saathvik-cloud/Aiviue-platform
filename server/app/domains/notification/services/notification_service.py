"""
Notification service: reacts to domain events and sends via configured channels (WATI first).
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.domains.employer.models import Employer
from app.domains.job.models import Job
from app.domains.notification.services.wati_client import WATIClient
from app.shared.database import async_session_factory
from app.shared.logging import get_logger
from app.shared.utils.phone import normalize_phone_to_e164

logger = get_logger(__name__) 


class NotificationService:
    """
    Sends notifications based on domain events.
    Uses WATI for WhatsApp; email/SMS can be added later.
    """

    def __init__(
        self,
        wati_client: WATIClient | None,
        template_job_published: str = "welcome",
        default_phone_country_code: str = "91",
    ) -> None:
        self.wati = wati_client
        self.template_job_published = template_job_published
        self.default_phone_country_code = default_phone_country_code

    async def send_job_published_whatsapp(
        self,
        job_id: str,
        employer_id: str,
        job_title: str,
    ) -> bool:
        """
        Send "job published" WhatsApp notification to the employer using the configured template.

        Loads employer (phone, name, company_name) and sends via WATI.
        If employer has no phone or WATI is not configured, logs and returns False.
        """
        if not self.wati:
            logger.debug("WATI not configured - skipping job published notification")
            return False

        job_uuid = UUID(job_id)
        employer_uuid = UUID(employer_id)

        async with async_session_factory() as session:
            job = await session.execute(
                select(Job)
                .where(Job.id == job_uuid)
                .options(selectinload(Job.employer))
            )
            job = job.scalar_one_or_none()
            if not job or not job.employer:
                logger.warning(
                    "Job or employer not found for notification",
                    extra={"job_id": job_id, "employer_id": employer_id},
                )
                return False

            employer = job.employer
            raw_phone = (employer.phone or "").strip()
            if not raw_phone:
                logger.info(
                    "Employer has no phone - skipping WhatsApp notification",
                    extra={"employer_id": employer_id},
                )
                return False
            phone = normalize_phone_to_e164(
                raw_phone,
                default_country_code=self.default_phone_country_code,
            )
            if not phone:
                logger.warning(
                    "Employer phone could not be normalized - skipping WhatsApp",
                    extra={"employer_id": employer_id},
                )
                return False

            # Template "welcome" typically has {{name}} and {{job_name}} (or similar)
            parameters = [
                {"name": "name", "value": employer.name or "Employer"},
                {"name": "job_name", "value": job_title or job.title},
            ]
            # If template uses "company" instead of job_name, add it; client can send multiple params
            parameters.append({"name": "company", "value": employer.company_name or ""})

            result = await self.wati.send_template(
                template_name=self.template_job_published,
                whatsapp_number=phone,
                parameters=parameters,
                broadcast_name="job_published",
            )
            return result is not None
