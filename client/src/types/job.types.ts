/**
 * Job Types
 */

import type { BaseEntity } from './api.types';

// Job Status
export type JobStatus = 'draft' | 'published' | 'closed' | 'paused';

// Work Type
export type WorkType = 'onsite' | 'remote' | 'hybrid';

// Currency Type
export type Currency = 'INR' | 'USD' | 'EUR' | 'GBP' | 'AUD' | 'CAD';

// Job Entity
export interface Job extends BaseEntity {
  employer_id: string;
  employer_name?: string | null; // Company/employer name for job detail
  title: string;
  description: string;
  requirements?: string;
  location?: string;
  city?: string;
  state?: string;
  country?: string;
  work_type?: WorkType;
  salary_range_min?: number;
  salary_range_max?: number;
  currency?: Currency;
  salary_range?: string;
  experience_min?: number;
  experience_max?: number;
  experience_range?: string;
  shift_preferences?: Record<string, unknown>;
  openings_count: number;
  status: JobStatus;
  is_published: boolean;
  is_draft: boolean;
  published_at?: string;
  closed_at?: string;
  close_reason?: string;
}

// Create Job Request
export interface CreateJobRequest {
  employer_id: string;
  title: string;
  description: string;
  requirements?: string;
  location?: string;
  city?: string;
  state?: string;
  country?: string;
  work_type?: WorkType;
  salary_range_min?: number;
  salary_range_max?: number;
  currency?: Currency;
  experience_min?: number;
  experience_max?: number;
  shift_preferences?: Record<string, unknown>;
  openings_count?: number;
  idempotency_key?: string;
}

// Update Job Request
export interface UpdateJobRequest {
  title?: string;
  description?: string;
  requirements?: string;
  location?: string;
  city?: string;
  state?: string;
  country?: string;
  work_type?: WorkType;
  salary_range_min?: number;
  salary_range_max?: number;
  currency?: Currency;
  experience_min?: number;
  experience_max?: number;
  shift_preferences?: Record<string, unknown>;
  openings_count?: number;
  version: number;
}

// Publish/Close Requests
export interface PublishJobRequest {
  version: number;
}

export interface CloseJobRequest {
  version: number;
  reason?: string;
}

// Job Filters
export interface JobFilters {
  employer_id?: string;
  status?: JobStatus;
  work_type?: WorkType;
  search?: string;
  is_active?: boolean;
  category_id?: string;
  role_id?: string;
  city?: string;
  state?: string;
}

// Job Summary (for lists)
export interface JobSummary {
  id: string;
  employer_id: string;
  employer_name?: string | null; // Company/employer name for job cards
  title: string;
  location?: string;
  work_type?: WorkType;
  salary_range?: string;
  status: JobStatus;
  openings_count: number;
  created_at: string;
}

// Job Stats
export interface JobStats {
  total: number;
  published: number;
  draft: number;
  closed: number;
}
