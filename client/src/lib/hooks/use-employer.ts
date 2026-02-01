/**
 * Employer Hooks - TanStack Query hooks for employer operations
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as employerService from '@/services/employer.service';
import type { CreateEmployerRequest, UpdateEmployerRequest } from '@/types';

// Query keys
export const employerKeys = {
  all: ['employers'] as const,
  byId: (id: string) => [...employerKeys.all, 'byId', id] as const,
  byEmail: (email: string) => [...employerKeys.all, 'byEmail', email] as const,
};

// Get employer by ID
export function useEmployer(id: string | undefined) {
  return useQuery({
    queryKey: employerKeys.byId(id || ''),
    queryFn: () => employerService.getEmployerById(id!),
    enabled: !!id,
  });
}

// Get employer by email
export function useEmployerByEmail(email: string | undefined) {
  return useQuery({
    queryKey: employerKeys.byEmail(email || ''),
    queryFn: () => employerService.getEmployerByEmail(email!),
    enabled: !!email,
    retry: false, // Don't retry on 404
  });
}

// Create employer mutation
export function useCreateEmployer() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateEmployerRequest) => employerService.createEmployer(data),
    onSuccess: (employer) => {
      // Invalidate and refetch
      queryClient.invalidateQueries({ queryKey: employerKeys.all });
      // Set cache for this employer
      queryClient.setQueryData(employerKeys.byId(employer.id), employer);
      queryClient.setQueryData(employerKeys.byEmail(employer.email), employer);
    },
  });
}

// Update employer mutation
export function useUpdateEmployer() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateEmployerRequest }) =>
      employerService.updateEmployer(id, data),
    onSuccess: (employer) => {
      queryClient.setQueryData(employerKeys.byId(employer.id), employer);
      queryClient.setQueryData(employerKeys.byEmail(employer.email), employer);
    },
  });
}
