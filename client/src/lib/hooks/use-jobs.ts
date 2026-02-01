/**
 * Job Hooks - TanStack Query hooks for job operations
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as jobService from '@/services/job.service';
import type {
  CreateJobRequest,
  UpdateJobRequest,
  PublishJobRequest,
  CloseJobRequest,
  JobFilters,
} from '@/types';

// Query keys
export const jobKeys = {
  all: ['jobs'] as const,
  list: (filters?: JobFilters) => [...jobKeys.all, 'list', filters] as const,
  byId: (id: string) => [...jobKeys.all, 'byId', id] as const,
  stats: (employerId: string) => [...jobKeys.all, 'stats', employerId] as const,
};

// Get job by ID
export function useJob(id: string | undefined) {
  return useQuery({
    queryKey: jobKeys.byId(id || ''),
    queryFn: () => jobService.getJobById(id!),
    enabled: !!id,
  });
}

// List jobs
export function useJobs(filters?: JobFilters, cursor?: string, limit?: number) {
  return useQuery({
    queryKey: jobKeys.list(filters),
    queryFn: () => jobService.listJobs(filters, cursor, limit, true),
  });
}

// Get job stats
export function useJobStats(employerId: string | undefined) {
  return useQuery({
    queryKey: jobKeys.stats(employerId || ''),
    queryFn: () => jobService.getJobStats(employerId!),
    enabled: !!employerId,
  });
}

// Create job mutation
export function useCreateJob() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateJobRequest) => jobService.createJob(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: jobKeys.all });
    },
  });
}

// Update job mutation
export function useUpdateJob() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateJobRequest }) =>
      jobService.updateJob(id, data),
    onSuccess: (job) => {
      queryClient.setQueryData(jobKeys.byId(job.id), job);
      queryClient.invalidateQueries({ queryKey: jobKeys.list() });
    },
  });
}

// Publish job mutation
export function usePublishJob() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: PublishJobRequest }) =>
      jobService.publishJob(id, data),
    onSuccess: (job) => {
      queryClient.setQueryData(jobKeys.byId(job.id), job);
      queryClient.invalidateQueries({ queryKey: jobKeys.all });
    },
  });
}

// Close job mutation
export function useCloseJob() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: CloseJobRequest }) =>
      jobService.closeJob(id, data),
    onSuccess: (job) => {
      queryClient.setQueryData(jobKeys.byId(job.id), job);
      queryClient.invalidateQueries({ queryKey: jobKeys.all });
    },
  });
}

// Delete job mutation
export function useDeleteJob() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, version }: { id: string; version: number }) =>
      jobService.deleteJob(id, version),
    onSuccess: (_, { id }) => {
      queryClient.removeQueries({ queryKey: jobKeys.byId(id) });
      queryClient.invalidateQueries({ queryKey: jobKeys.all });
    },
  });
}
