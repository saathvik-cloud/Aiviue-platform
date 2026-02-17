/**
 * Candidate Types
 *
 * TypeScript types for the candidate module.
 * Mirrors backend Pydantic schemas (candidate domain).
 */

import type { BaseEntity } from './api.types';

// ==================== CONSTANTS ====================

export type ProfileStatus = 'basic' | 'complete';
export type ResumeStatus = 'in_progress' | 'completed' | 'invalidated';
export type ResumeSource = 'aivi_bot' | 'pdf_upload';

// ==================== CANDIDATE ENTITY ====================

export interface Candidate extends BaseEntity {
  mobile: string;
  name: string;
  email?: string;
  profile_photo_url?: string;
  date_of_birth?: string;
  preferred_job_category_id?: string;
  preferred_job_role_id?: string;
  current_location?: string;
  preferred_job_location?: string;
  languages_known?: string[];
  about?: string;
  current_monthly_salary?: number;
  /** Years of experience (for job recommendations). From API when available. */
  years_experience?: number;
  /** Relevant skills text or comma-separated (for job recommendations). From API when available. */
  relevant_skills?: string;
  aadhaar_number_encrypted?: string;
  pan_number_encrypted?: string;
  /** Profile/onboarding completion (basic | complete). Distinct from has_resume. */
  profile_status: ProfileStatus;
  /** True if candidate has at least one completed resume. From API when available. */
  has_resume?: boolean;
  /** Version of latest resume, if any. From API when available. */
  latest_resume_version?: number;
  /** Pro: unlimited AIVI bot resumes; free: gated by resume_remaining_count. */
  is_pro?: boolean;
  /** Remaining free AIVI bot uses; 0 = upgrade required. Default 1. */
  resume_remaining_count?: number;
}

// ==================== CANDIDATE RESUME ====================

export interface CandidateResume {
  id: string;
  candidate_id: string;
  resume_data?: Record<string, any>;
  pdf_url?: string;
  source: ResumeSource;
  status: ResumeStatus;
  version_number: number;
  chat_session_id?: string;
  created_at: string;
  updated_at: string;
}

// ==================== REQUEST TYPES ====================

/** Signup: mobile, name, current location, preferred location only. Category/role filled later (e.g. from resume). */
export interface CandidateSignupRequest {
  mobile: string;
  name: string;
  current_location: string;
  preferred_location: string;
}

export interface CandidateLoginRequest {
  mobile: string;
}

const UUID_REGEX = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

export function isUuid(s: string | undefined): boolean {
  return !!s && UUID_REGEX.test(s.trim());
}

export interface CandidateBasicProfileRequest {
  name: string;
  current_location?: string;
  preferred_job_category_id?: string;
  preferred_job_role_id?: string;
  preferred_job_role_custom?: string;
  preferred_job_location?: string;
}

export interface CandidateUpdateRequest {
  name?: string;
  email?: string;
  profile_photo_url?: string;
  date_of_birth?: string;
  current_location?: string;
  preferred_job_category_id?: string;
  preferred_job_role_id?: string;
  preferred_job_role_custom?: string;
  preferred_job_location?: string;
  languages_known?: string[];
  about?: string;
  current_monthly_salary?: number;
  aadhaar_number?: string;
  pan_number?: string;
  version: number;
}

// ==================== RESPONSE TYPES ====================

export interface CandidateAuthResponse {
  candidate: Candidate;
  is_new: boolean;
  message: string;
}

export interface CandidateSummaryResponse {
  id: string;
  name: string;
  mobile: string;
  profile_status: ProfileStatus;
  has_resume: boolean;
  latest_resume_version?: number;
}

// ==================== JOB MASTER TYPES ====================

export interface JobCategory {
  id: string;
  name: string;
  slug: string;
  description?: string;
  icon?: string;
  display_order: number;
  is_active: boolean;
  roles?: JobRole[];
}

export interface JobRole {
  id: string;
  name: string;
  slug: string;
  job_type: 'blue_collar' | 'white_collar';
  description?: string;
  is_active: boolean;
  categories?: JobCategory[];
}

export interface RoleQuestionTemplate {
  id: string;
  role_id: string;
  question_key: string;
  question_text: string;
  question_type: string;
  is_required: boolean;
  display_order: number;
  options?: any;
  validation_rules?: Record<string, any>;
  condition?: Record<string, any>;
  is_active: boolean;
}

// ==================== JOB RECOMMENDATION ====================

export interface JobRecommendation {
  id: string;
  title: string;
  company_name: string;
  location?: string;
  salary_min?: number;
  salary_max?: number;
  work_type?: string;
  match_score?: number;
  posted_at: string;
}
