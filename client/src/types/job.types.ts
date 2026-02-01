/**
 * Job Types
 */

import type { BaseEntity } from './api.types';

// Job Status
export type JobStatus = 'draft' | 'published' | 'closed' | 'paused';

// Work Type
export type WorkType = 'onsite' | 'remote' | 'hybrid';

// Job Entity
export interface Job extends BaseEntity {
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
  salary_range?: string;
  compensation?: string;
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
  compensation?: string;
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
  compensation?: string;
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
}

// Job Summary (for lists)
export interface JobSummary {
  id: string;
  employer_id: string;
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
