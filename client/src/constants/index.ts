/**
 * Constants Index
 */

export * from './api-endpoints';
export * from './routes';
export * from './state_cities';
export * from './ui';

// App-wide constants
export const APP_NAME = 'AIVIUE';
export const APP_DESCRIPTION = 'AI-Powered Hiring Platform';

// Pagination defaults
export const DEFAULT_PAGE_SIZE = 20;
export const MAX_PAGE_SIZE = 100;

// Polling intervals (ms)
export const EXTRACTION_POLL_INTERVAL = 2000;
export const EXTRACTION_MAX_POLLS = 60;

// Form validation
export const VALIDATION = {
  EMAIL_REGEX: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
  PHONE_REGEX: /^\+?[\d\s-]{10,}$/,
  MIN_JD_LENGTH: 50,
  MAX_JD_LENGTH: 10000,
  MIN_TITLE_LENGTH: 3,
  MAX_TITLE_LENGTH: 200,
} as const;

// Job statuses
export const JOB_STATUS = {
  DRAFT: 'draft',
  PUBLISHED: 'published',
  CLOSED: 'closed',
  PAUSED: 'paused',
} as const;

// Work types
export const WORK_TYPES = [
  { value: 'onsite', label: 'On-site' },
  { value: 'remote', label: 'Remote' },
  { value: 'hybrid', label: 'Hybrid' },
] as const;

// Company sizes (must match backend enum: startup, small, medium, large, enterprise)
export const COMPANY_SIZES = [
  { value: 'startup', label: '1-10 employees (Startup)' },
  { value: 'small', label: '11-50 employees (Small)' },
  { value: 'medium', label: '51-200 employees (Medium)' },
  { value: 'large', label: '201-1000 employees (Large)' },
  { value: 'enterprise', label: '1000+ employees (Enterprise)' },
] as const;

// Extraction statuses
export const EXTRACTION_STATUS = {
  PENDING: 'pending',
  PROCESSING: 'processing',
  COMPLETED: 'completed',
  FAILED: 'failed',
} as const;

// ==================== CANDIDATE CONSTANTS ====================

// Candidate mobile validation
export const CANDIDATE_VALIDATION = {
  MOBILE_REGEX: /^[6-9]\d{9}$/,  // Indian mobile number (10 digits, starts with 6-9)
  MOBILE_MIN_LENGTH: 10,
  MOBILE_MAX_LENGTH: 10,
  NAME_MIN_LENGTH: 2,
  NAME_MAX_LENGTH: 100,
  ABOUT_MAX_LENGTH: 500,
  PROFILE_PHOTO_MAX_SIZE_MB: 2,
  RESUME_PDF_MAX_SIZE_MB: 2,
  /** Max length for current_location / preferred_job_location (matches backend String(255)) */
  LOCATION_MAX_LENGTH: 255,
} as const;

// Profile statuses
export const PROFILE_STATUS = {
  BASIC: 'basic',
  COMPLETE: 'complete',
} as const;

// Resume statuses
export const RESUME_STATUS = {
  IN_PROGRESS: 'in_progress',
  COMPLETED: 'completed',
  INVALIDATED: 'invalidated',
} as const;

// Resume sources
export const RESUME_SOURCE = {
  AIVI_BOT: 'aivi_bot',
  PDF_UPLOAD: 'pdf_upload',
} as const;

// Candidate chat steps (mirrors backend ChatStep)
export const CHAT_STEP = {
  WELCOME: 'welcome',
  CHOOSE_METHOD: 'choose_method',
  UPLOAD_RESUME: 'upload_resume',
  EXTRACTION_PROCESSING: 'extraction_processing',
  MISSING_FIELDS: 'missing_fields',
  ASKING_QUESTIONS: 'asking_questions',
  RESUME_PREVIEW: 'resume_preview',
  COMPLETED: 'completed',
} as const;

// WebSocket reconnect settings
export const WS_CONFIG = {
  RECONNECT_DELAY_MS: 2000,
  MAX_RECONNECT_ATTEMPTS: 5,
  PING_INTERVAL_MS: 30000,
} as const;
