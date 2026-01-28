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
