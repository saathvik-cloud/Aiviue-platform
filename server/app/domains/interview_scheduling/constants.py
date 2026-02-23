"""
Constants for interview scheduling domain.

- WATI template keys: used in code to decide which template to send; actual name comes from settings.
- Slot/availability constraints: allowed values per spec.
"""

# WATI template types (map to settings: wati_template_interview_*)
WATI_TEMPLATE_SLOTS_OFFERED = "slots_offered"
WATI_TEMPLATE_MEET_LINK = "meet_link"
WATI_TEMPLATE_CANDIDATE_CHOSE_SLOT = "candidate_chose_slot"
WATI_TEMPLATE_CANCELLED = "cancelled"

# Slot duration choices (minutes) - per spec
SLOT_DURATION_CHOICES = (15, 30, 45)

# Buffer between slots (minutes) - per spec
BUFFER_CHOICES = (5, 10, 15, 30)

# Slot generation window (days) - per spec
SLOT_GENERATION_DAYS = 14

# Offer expiry: candidate must respond within 48h (effective_expiry = min(48h, earliest_slot_start - X))
OFFER_EXPIRY_HOURS = 48
OFFER_EXPIRY_MINUTES_BEFORE_SLOT = 15  # X in spec

# Employer must confirm within 24h of candidate confirmation
EMPLOYER_CONFIRM_TIMEOUT_HOURS = 24

# Cancellation detection polling interval (minutes)
CALENDAR_POLL_INTERVAL_MINUTES = 15
