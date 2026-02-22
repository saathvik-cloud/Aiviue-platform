"""
Interview scheduling domain.

Platform acts as middleman: one Google account creates Meet links,
adds employer and candidate as attendees. Employer sets availability;
employer sends slots to candidate; candidate confirms; employer confirms;
we create event and send link (email + WATI when templates are set).

Structure:
- models/     SQLAlchemy: EmployerAvailability, InterviewSchedule, InterviewOfferedSlot
- schemas/    Pydantic request/response
- repository/ Data access (availability, interview_schedule)
- services/   Business logic (slot generation, state machine)
- api/        Routes (employer + candidate flow)
- clients/    Google Calendar client (create Meet, patch cancelled, get for polling)
"""
