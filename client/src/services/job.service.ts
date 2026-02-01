/**
 * Job Service - API calls for job operations
 */

import { get, post, put, del } from '@/lib/api';
import { API_ENDPOINTS, buildQueryParams } from '@/constants';
import type {
  Job,
  JobSummary,
  CreateJobRequest,
  UpdateJobRequest,
  PublishJobRequest,
  CloseJobRequest,
  JobFilters,
  PaginatedResponse,
} from '@/types';

// Get job by ID
export async function getJobById(id: string): Promise<Job> {
  return get<Job>(API_ENDPOINTS.JOBS.BY_ID(id));
}

// Create job
export async function createJob(data: CreateJobRequest): Promise<Job> {
  return post<Job>(API_ENDPOINTS.JOBS.BASE, data);
}

// Update job
export async function updateJob(id: string, data: UpdateJobRequest): Promise<Job> {
  return put<Job>(API_ENDPOINTS.JOBS.BY_ID(id), data);
}

// Delete job
export async function deleteJob(id: string, version: number): Promise<void> {
  return del<void>(`${API_ENDPOINTS.JOBS.BY_ID(id)}?version=${version}`);
}

// Publish job
export async function publishJob(id: string, data: PublishJobRequest): Promise<Job> {
  return post<Job>(API_ENDPOINTS.JOBS.PUBLISH(id), data);
}

// Close job
export async function closeJob(id: string, data: CloseJobRequest): Promise<Job> {
  return post<Job>(API_ENDPOINTS.JOBS.CLOSE(id), data);
}

// List jobs
export async function listJobs(
  filters?: JobFilters,
  cursor?: string,
  limit?: number,
  includeTotal?: boolean
): Promise<PaginatedResponse<JobSummary>> {
  const params = buildQueryParams({
    ...filters,
    cursor,
    limit,
    include_total: includeTotal,
  });
  return get<PaginatedResponse<JobSummary>>(`${API_ENDPOINTS.JOBS.BASE}${params}`);
}

// Get job stats for dashboard
export async function getJobStats(employerId: string): Promise<{
  total: number;
  published: number;
  draft: number;
  closed: number;
}> {
  // Fetch jobs with status counts
  const [published, draft, closed] = await Promise.all([
    listJobs({ employer_id: employerId, status: 'published' }, undefined, 1, true),
    listJobs({ employer_id: employerId, status: 'draft' }, undefined, 1, true),
    listJobs({ employer_id: employerId, status: 'closed' }, undefined, 1, true),
  ]);

  return {
    total: (published.total_count || 0) + (draft.total_count || 0) + (closed.total_count || 0),
    published: published.total_count || 0,
    draft: draft.total_count || 0,
    closed: closed.total_count || 0,
  };
}
