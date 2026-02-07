/**
 * Candidate Service - API calls for candidate operations.
 *
 * Handles candidate authentication (mobile-based), profile management,
 * and resume retrieval.
 */

import { API_ENDPOINTS, buildQueryParams } from '@/constants';
import { get, post, put } from '@/lib/api';
import type {
    Candidate,
    CandidateAuthResponse,
    CandidateBasicProfileRequest,
    CandidateLoginRequest,
    CandidateResume,
    CandidateSignupRequest,
    CandidateUpdateRequest,
    JobCategory,
    JobRole
} from '@/types';

// ==================== AUTH ====================

/**
 * Signup a new candidate.
 * Creates a new candidate with mobile + basic profile info.
 */
export async function candidateSignup(
  data: CandidateSignupRequest
): Promise<CandidateAuthResponse> {
  return post<CandidateAuthResponse>(API_ENDPOINTS.CANDIDATES.SIGNUP, data);
}

/**
 * Login an existing candidate by mobile number.
 * Returns candidate data if mobile exists, error if not.
 */
export async function candidateLogin(
  data: CandidateLoginRequest
): Promise<CandidateAuthResponse> {
  return post<CandidateAuthResponse>(API_ENDPOINTS.CANDIDATES.LOGIN, data);
}

/**
 * Get candidate by mobile number.
 * Used for checking if mobile already exists during signup.
 */
export async function getCandidateByMobile(mobile: string): Promise<Candidate> {
  return get<Candidate>(API_ENDPOINTS.CANDIDATES.BY_MOBILE(mobile));
}

// ==================== PROFILE ====================

/**
 * Get candidate by ID.
 */
export async function getCandidateById(id: string): Promise<Candidate> {
  return get<Candidate>(API_ENDPOINTS.CANDIDATES.BY_ID(id));
}

/**
 * Create basic profile (mandatory after signup).
 * Required: name, current_location, preferred_job_category_id, preferred_job_role_id, preferred_job_location.
 */
export async function createBasicProfile(
  candidateId: string,
  data: CandidateBasicProfileRequest
): Promise<Candidate> {
  return post<Candidate>(API_ENDPOINTS.CANDIDATES.BASIC_PROFILE(candidateId), data);
}

/**
 * Update candidate profile.
 * Requires version for optimistic locking.
 */
export async function updateCandidate(
  id: string,
  data: CandidateUpdateRequest
): Promise<Candidate> {
  return put<Candidate>(API_ENDPOINTS.CANDIDATES.BY_ID(id), data);
}

// ==================== RESUME ====================

/**
 * Get latest resume for a candidate.
 */
export async function getLatestResume(candidateId: string): Promise<CandidateResume> {
  return get<CandidateResume>(API_ENDPOINTS.CANDIDATES.RESUME(candidateId));
}

/**
 * List all resumes for a candidate (newest first).
 */
export async function getResumes(candidateId: string): Promise<CandidateResume[]> {
  return get<CandidateResume[]>(API_ENDPOINTS.CANDIDATES.RESUMES(candidateId));
}

/**
 * Get a specific resume by ID (must belong to candidate).
 */
export async function getResumeById(
  candidateId: string,
  resumeId: string
): Promise<CandidateResume> {
  return get<CandidateResume>(API_ENDPOINTS.CANDIDATES.RESUME_BY_ID(candidateId, resumeId));
}

// ==================== JOB MASTER ====================

/**
 * Get all job categories (with roles).
 * Backend returns { items: JobCategory[], total_count: number }.
 */
export async function getJobCategories(): Promise<JobCategory[]> {
  const res = await get<{ items: JobCategory[]; total_count: number }>(
    API_ENDPOINTS.JOB_MASTER.CATEGORIES
  );
  return res?.items ?? [];
}

/**
 * Get roles for a specific category.
 */
export async function getRolesByCategory(categoryId: string): Promise<JobRole[]> {
  return get<JobRole[]>(API_ENDPOINTS.JOB_MASTER.ROLES_BY_CATEGORY(categoryId));
}

/**
 * Get all job roles.
 */
export async function getJobRoles(jobType?: string): Promise<JobRole[]> {
  const params = buildQueryParams({ job_type: jobType });
  return get<JobRole[]>(`${API_ENDPOINTS.JOB_MASTER.ROLES}${params}`);
}

/**
 * Search roles by name (for autocomplete).
 */
export async function searchRoles(
  searchTerm: string,
  limit: number = 10
): Promise<JobRole[]> {
  const params = buildQueryParams({ q: searchTerm, limit });
  return get<JobRole[]>(`${API_ENDPOINTS.JOB_MASTER.SEARCH_ROLES}${params}`);
}
