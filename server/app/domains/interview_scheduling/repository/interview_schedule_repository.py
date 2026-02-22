"""
Repository for interview_schedules and interview_offered_slots.

State machine updates, slot CRUD. To be implemented in Step 6.
"""

# from sqlalchemy.ext.asyncio import AsyncSession
# from app.domains.interview_scheduling.models import InterviewSchedule, InterviewOfferedSlot

# class InterviewScheduleRepository:
#     def __init__(self, session: AsyncSession) -> None:
#         self._session = session
#     async def get_by_application_id(self, application_id: UUID) -> InterviewSchedule | None: ...
#     async def create(self, ...) -> InterviewSchedule: ...
#     async def update_state(self, ...) -> InterviewSchedule: ...
