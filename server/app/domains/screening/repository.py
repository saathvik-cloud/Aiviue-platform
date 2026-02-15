"""
Screening domain repository for Aiviue Platform.

Repository for screening_dead_letters table.
"""

from typing import Any, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.screening.models import ScreeningDeadLetter
from app.shared.logging import get_logger


logger = get_logger(__name__)


class ScreeningDeadLetterRepository:
    """Repository for ScreeningDeadLetter (dead letter table)."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, data: dict[str, Any]) -> ScreeningDeadLetter:
        """Insert a failed payload into dead letter table."""
        record = ScreeningDeadLetter(**data)
        self.session.add(record)
        await self.session.flush()
        await self.session.refresh(record)
        logger.debug(
            "Screening dead letter created",
            extra={"id": str(record.id), "error_code": record.error_code},
        )
        return record

    async def list(
        self,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[ScreeningDeadLetter], int]:
        """
        List dead letter records, optionally filtered by status.
        Returns (items, total_count).
        """
        base = select(ScreeningDeadLetter)
        count_query = select(func.count()).select_from(ScreeningDeadLetter)
        if status:
            base = base.where(ScreeningDeadLetter.status == status)
            count_query = count_query.where(ScreeningDeadLetter.status == status)

        base = base.order_by(ScreeningDeadLetter.created_at.desc()).offset(offset).limit(limit)
        result = await self.session.execute(base)
        items = list(result.scalars().all())

        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        return items, total
