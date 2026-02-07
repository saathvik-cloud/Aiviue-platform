# API Constants
API_V1_PREFIX = "/api/v1"

# Database
DB_POOL_SIZE = 5
DB_MAX_OVERFLOW = 10
DB_POOL_TIMEOUT = 30

# Job Status
class JobStatus:
    DRAFT = "draft"
    PUBLISHED = "published"
    PAUSED = "paused"
    CLOSED = "closed"

# Work Type
class WorkType:
    REMOTE = "remote"
    HYBRID = "hybrid"
    ONSITE = "onsite"

# Shift Type
class ShiftType:
    GENERAL = "general"
    ROTATIONAL = "rotational"
    NIGHT = "night"
    FLEXIBLE = "flexible"

# Candidate Profile Status
class CandidateProfileStatus:
    BASIC = "basic"
    COMPLETE = "complete"

# Candidate Resume Status
class CandidateResumeStatus:
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    INVALIDATED = "invalidated"

# Candidate Resume Source
class CandidateResumeSource:
    AIVI_BOT = "aivi_bot"
    PDF_UPLOAD = "pdf_upload"

# Job Type Classification
class JobTypeClassification:
    BLUE_COLLAR = "blue_collar"
    WHITE_COLLAR = "white_collar"

# File Upload Limits
PROFILE_PHOTO_MAX_SIZE_MB = 2
RESUME_PDF_MAX_SIZE_MB = 2
