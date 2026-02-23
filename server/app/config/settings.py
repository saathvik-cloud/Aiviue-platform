from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """
 
    # App Settings 
    app_name: str = "aiviue-backend"
    app_env: str = "development"
    debug: bool = True
    api_version: str = "v1"
    secret_key: str = "change-me-in-production"
    # Optional: dedicated key for Aadhaar/PAN encryption (defaults to secret_key)
    encryption_key: str | None = None
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Database
    database_url: str
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # LLM - Gemini
    gemini_api_key: str
    gemini_model: str = "gemini-2.5-flash"
    
    # CORS
    cors_origins: str = "http://localhost:3000"
    
    # Logging
    log_level: str = "INFO"
    
    # Feature Flags
    enable_screening_events: bool = False  # Set True when Screening Agent is ready

    # WATI (WhatsApp) - for notification module
    wati_api_endpoint: str | None = None  # e.g. https://live-mt-server.wati.io/105961
    wati_api_token: str | None = None  # Bearer token
    wati_channel_number: str | None = None  # Sender WhatsApp number (E.164)
    wati_template_job_published: str = "welcome"  # Template name for job published notification
    default_phone_country_code: str = "91"  # E.164 country code when normalizing phone numbers (e.g. India)

    # Notification module - consume job.published from stream and send WhatsApp
    enable_notification_consumer: bool = True  # Set False to disable in-process consumer

    # Screening Agent API - when set, screening endpoints require X-Api-Key header
    screening_api_key: str | None = None

    # Interview scheduling - Google Calendar + Meet
    # Flag: True = use service account (Workspace), False = use OAuth (client ID + secret + refresh token)
    google_use_service_account: bool = False
    # OAuth 2.0 credentials (when google_use_service_account=False): full Meet + attendees + email invites
    google_oauth_client_id: str | None = None
    google_oauth_client_secret: str | None = None
    google_oauth_refresh_token: str | None = None
    # Service Account credentials (when google_use_service_account=True): limited Meet/attendees
    google_service_account_json: str | None = None
    # Calendar ID: use "primary" for OAuth, or a specific calendar ID for service accounts
    google_calendar_id: str = "primary"

    # Interview scheduling - WATI template names (optional until templates approved)
    # When set, interview flow will send WhatsApp messages via these templates; when empty, in-app only
    wati_template_interview_slots_offered: str | None = None
    wati_template_interview_meet_link: str | None = None
    wati_template_interview_candidate_chose_slot: str | None = None
    wati_template_interview_cancelled: str | None = None
    enable_interview_scheduling_jobs: bool = True  # Background jobs: offer expiry, employer timeout, calendar poll

    # Storage (optional - for resume PDF upload)
    supabase_url: str | None = None
    supabase_service_role_key: str | None = None
    supabase_resume_bucket: str = "resumes"
    # Allowed origins for resume PDF URLs (SSRF protection). Comma-separated; if empty and supabase_url set, uses that host.
    allowed_pdf_origins: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    @property
    def cors_origins_list(self) -> list[str]:
        """Convert comma-separated CORS origins to list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def allowed_pdf_origins_list(self) -> list[str]:
        """Origins allowed for resume PDF URLs (SSRF protection). Defaults to supabase_url host if set."""
        if self.allowed_pdf_origins:
            return [o.strip() for o in self.allowed_pdf_origins.split(",") if o.strip()]
        if self.supabase_url:
            from urllib.parse import urlparse
            parsed = urlparse(self.supabase_url)
            if parsed.scheme and parsed.netloc:
                return [f"{parsed.scheme}://{parsed.netloc}"]
        return []
    
    @property
    def is_development(self) -> bool:
        return self.app_env == "development"
    
    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Using lru_cache ensures settings are only loaded once.
    """
    return Settings()


# Global settings instance for easy import
settings = get_settings()
