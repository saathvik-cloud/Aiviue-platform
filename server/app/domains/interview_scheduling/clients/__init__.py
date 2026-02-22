"""
Interview scheduling external clients.

Google Calendar client for creating Meet events, patching cancelled, and get (polling).
"""

from app.domains.interview_scheduling.clients.google_calendar import GoogleCalendarClient

__all__ = ["GoogleCalendarClient"]
