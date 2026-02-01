/**
 * Constants Index
 */

export * from './routes';
export * from './api-endpoints';

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
