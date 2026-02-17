/**
 * Application Hooks - TanStack Query hooks for job application operations
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as applicationService from '@/services/application.service';
import { jobKeys } from './use-jobs';

// Query keys
export const applicationKeys = {
  all: ['applications'] as const,
  appliedJobIds: ['applications', 'appliedJobIds'] as const,
  appliedJobsList: ['applications', 'appliedJobsList'] as const,
  list: (jobId: string) => [...applicationKeys.all, 'list', jobId] as const,
  detail: (jobId: string, applicationId: string) =>
    [...applicationKeys.all, 'detail', jobId, applicationId] as const,
};

// Get job IDs the current candidate has applied to
export function useAppliedJobIds(candidateId: string | undefined) {
  return useQuery({
    queryKey: applicationKeys.appliedJobIds,
    queryFn: () => applicationService.getAppliedJobIds(),
    enabled: !!candidateId,
  });
}

// List applied jobs for current candidate (paginated, recent first)
export function useAppliedJobsList(
  candidateId: string | undefined,
  cursor?: string,
  limit: number = 20
) {
  return useQuery({
    queryKey: [...applicationKeys.appliedJobsList, cursor ?? '', limit],
    queryFn: () => applicationService.listAppliedJobs(cursor, limit),
    enabled: !!candidateId,
  });
}

// List applications for a job
export function useApplicationsForJob(jobId: string | undefined) {
  return useQuery({
    queryKey: applicationKeys.list(jobId || ''),
    queryFn: () => applicationService.listApplications(jobId!),
    enabled: !!jobId,
  });
}

// Get application detail
export function useApplicationDetail(
  jobId: string | undefined,
  applicationId: string | undefined
) {
  return useQuery({
    queryKey: applicationKeys.detail(jobId || '', applicationId || ''),
    queryFn: () =>
      applicationService.getApplicationDetail(jobId!, applicationId!),
    enabled: !!jobId && !!applicationId,
  });
}

// Apply to job (candidate)
export function useApplyToJob() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      jobId,
      data,
    }: {
      jobId: string;
      data?: applicationService.JobApplyRequest;
    }) => applicationService.applyToJob(jobId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: applicationKeys.all });
      queryClient.invalidateQueries({ queryKey: applicationKeys.appliedJobIds });
      queryClient.invalidateQueries({ queryKey: applicationKeys.appliedJobsList });
      queryClient.invalidateQueries({ queryKey: jobKeys.all });
    },
  });
}
