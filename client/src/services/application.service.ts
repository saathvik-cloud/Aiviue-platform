/**
 * Application Service - API calls for job application management
 */

import { get, post } from '@/lib/api';
import { API_ENDPOINTS } from '@/constants';
import type {
  ApplicationListResponse,
  ApplicationDetailResponse,
  AppliedJobIdsResponse,
  JobApplyResponse,
} from '@/types';

export interface JobApplyRequest {
  resume_id?: string;
}

// Get job IDs the current candidate has applied to
export async function getAppliedJobIds(): Promise<AppliedJobIdsResponse> {
  return get<AppliedJobIdsResponse>(API_ENDPOINTS.CANDIDATES.APPLIED_JOBS);
}

// List applications for a job (employer)
export async function listApplications(
  jobId: string
): Promise<ApplicationListResponse> {
  return get<ApplicationListResponse>(
    API_ENDPOINTS.JOBS.APPLICATIONS(jobId)
  );
}

// Get application detail with candidate and resume (employer)
export async function getApplicationDetail(
  jobId: string,
  applicationId: string
): Promise<ApplicationDetailResponse> {
  return get<ApplicationDetailResponse>(
    API_ENDPOINTS.JOBS.APPLICATION_DETAIL(jobId, applicationId)
  );
}

// Apply to job (candidate)
export async function applyToJob(
  jobId: string,
  data?: JobApplyRequest
): Promise<JobApplyResponse> {
  return post<JobApplyResponse>(
    API_ENDPOINTS.JOBS.APPLY(jobId),
    data ?? {}
  );
}
