/**
 * Job Application Types
 *
 * Mirrors backend job_application domain schemas.
 */

import type { Candidate } from './candidate.types';
import type { CandidateResume } from './candidate.types';

export interface ApplicationListItem {
  id: string;
  job_id: string;
  candidate_id: string;
  applied_at: string;
  candidate_name: string;
  job_title: string;
  role_name?: string | null;
  resume_id?: string | null;
  has_resume_pdf: boolean;
}

export interface ApplicationListResponse {
  job_id: string;
  job_title: string;
  items: ApplicationListItem[];
}

export interface ApplicationDetailResponse {
  id: string;
  job_id: string;
  candidate_id: string;
  applied_at: string;
  candidate: Candidate;
  resume?: CandidateResume | null;
  resume_pdf_url?: string | null;
  resume_snapshot?: Record<string, unknown> | null;
}

export interface AppliedJobIdsResponse {
  job_ids: string[];
}

export interface JobApplyResponse {
  application_id: string;
  applied_at: string;
  already_applied: boolean;
  message: string;
}
