/**
 * Candidate Hooks - TanStack Query hooks for candidate operations.
 *
 * Follows the same pattern as employer hooks (use-employer.ts).
 */

import * as candidateService from '@/services/candidate.service';
import type {
    CandidateLoginRequest,
    CandidateSignupRequest,
    CandidateUpdateRequest,
} from '@/types';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

// ==================== QUERY KEYS ====================

export const candidateKeys = {
  all: ['candidates'] as const,
  byId: (id: string) => [...candidateKeys.all, 'byId', id] as const,
  byMobile: (mobile: string) => [...candidateKeys.all, 'byMobile', mobile] as const,
  resume: (candidateId: string) => [...candidateKeys.all, 'resume', candidateId] as const,
  resumes: (candidateId: string) => [...candidateKeys.all, 'resumes', candidateId] as const,
  resumeById: (candidateId: string, resumeId: string) =>
    [...candidateKeys.all, 'resume', candidateId, resumeId] as const,
  categories: ['jobCategories'] as const,
  roles: (categoryId?: string) => ['jobRoles', categoryId] as const,
  allRoles: (jobType?: string) => ['jobRoles', 'all', jobType] as const,
  searchRoles: (term: string) => ['jobRoles', 'search', term] as const,
};

// ==================== CANDIDATE QUERIES ====================

/**
 * Get candidate by ID.
 */
export function useCandidate(id: string | undefined) {
  return useQuery({
    queryKey: candidateKeys.byId(id || ''),
    queryFn: () => candidateService.getCandidateById(id!),
    enabled: !!id,
  });
}

/**
 * Get candidate by mobile number.
 */
export function useCandidateByMobile(mobile: string | undefined) {
  return useQuery({
    queryKey: candidateKeys.byMobile(mobile || ''),
    queryFn: () => candidateService.getCandidateByMobile(mobile!),
    enabled: !!mobile,
    retry: false,
  });
}

/**
 * Get latest resume for a candidate.
 */
export function useCandidateResume(candidateId: string | undefined) {
  return useQuery({
    queryKey: candidateKeys.resume(candidateId || ''),
    queryFn: () => candidateService.getLatestResume(candidateId!),
    enabled: !!candidateId,
    retry: false,
  });
}

/**
 * List all resumes for a candidate (resume history).
 */
export function useCandidateResumes(candidateId: string | undefined) {
  return useQuery({
    queryKey: candidateKeys.resumes(candidateId || ''),
    queryFn: () => candidateService.getResumes(candidateId!),
    enabled: !!candidateId,
  });
}

/**
 * Get a specific resume by ID.
 */
export function useCandidateResumeById(
  candidateId: string | undefined,
  resumeId: string | undefined
) {
  return useQuery({
    queryKey: candidateKeys.resumeById(candidateId || '', resumeId || ''),
    queryFn: () => candidateService.getResumeById(candidateId!, resumeId!),
    enabled: !!candidateId && !!resumeId,
  });
}

// ==================== CANDIDATE MUTATIONS ====================

/**
 * Signup a new candidate.
 */
export function useCandidateSignup() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CandidateSignupRequest) =>
      candidateService.candidateSignup(data),
    onSuccess: (response) => {
      const candidate = response.candidate;
      queryClient.setQueryData(candidateKeys.byId(candidate.id), candidate);
      queryClient.setQueryData(candidateKeys.byMobile(candidate.mobile), candidate);
    },
  });
}

/**
 * Login an existing candidate.
 */
export function useCandidateLogin() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CandidateLoginRequest) =>
      candidateService.candidateLogin(data),
    onSuccess: (response) => {
      const candidate = response.candidate;
      queryClient.setQueryData(candidateKeys.byId(candidate.id), candidate);
      queryClient.setQueryData(candidateKeys.byMobile(candidate.mobile), candidate);
    },
  });
}

/**
 * Update candidate profile.
 */
export function useUpdateCandidate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: CandidateUpdateRequest }) =>
      candidateService.updateCandidate(id, data),
    onSuccess: (candidate) => {
      queryClient.setQueryData(candidateKeys.byId(candidate.id), candidate);
      queryClient.setQueryData(candidateKeys.byMobile(candidate.mobile), candidate);
    },
  });
}

// ==================== JOB MASTER QUERIES ====================

/**
 * Get all job categories.
 */
export function useJobCategories() {
  return useQuery({
    queryKey: candidateKeys.categories,
    queryFn: () => candidateService.getJobCategories(),
    staleTime: 5 * 60 * 1000, // 5 minutes (master data changes rarely)
  });
}

/**
 * Get roles for a specific category.
 */
export function useRolesByCategory(categoryId: string | undefined) {
  return useQuery({
    queryKey: candidateKeys.roles(categoryId),
    queryFn: () => candidateService.getRolesByCategory(categoryId!),
    enabled: !!categoryId,
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * Get all job roles (optionally filtered by type).
 */
export function useJobRoles(jobType?: string) {
  return useQuery({
    queryKey: candidateKeys.allRoles(jobType),
    queryFn: () => candidateService.getJobRoles(jobType),
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * Search roles by name (for autocomplete).
 */
export function useSearchRoles(searchTerm: string) {
  return useQuery({
    queryKey: candidateKeys.searchRoles(searchTerm),
    queryFn: () => candidateService.searchRoles(searchTerm),
    enabled: searchTerm.length >= 2,
    staleTime: 30 * 1000,
  });
}
