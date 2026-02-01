/**
 * Extraction Hooks - TanStack Query hooks for JD extraction
 */

import { useQuery, useMutation } from '@tanstack/react-query';
import * as extractionService from '@/services/extraction.service';
import type { SubmitExtractionRequest, ExtractionResponse } from '@/types';

// Query keys
export const extractionKeys = {
  all: ['extractions'] as const,
  byId: (id: string) => [...extractionKeys.all, 'byId', id] as const,
};

// Get extraction status
export function useExtraction(id: string | undefined) {
  return useQuery({
    queryKey: extractionKeys.byId(id || ''),
    queryFn: () => extractionService.getExtractionStatus(id!),
    enabled: !!id,
    refetchInterval: (query) => {
      // Poll while pending/processing
      const status = query.state.data?.status;
      if (status === 'pending' || status === 'processing') {
        return 2000; // Poll every 2 seconds
      }
      return false; // Stop polling
    },
  });
}

// Submit extraction mutation
export function useSubmitExtraction() {
  return useMutation({
    mutationFn: (data: SubmitExtractionRequest) => extractionService.submitExtraction(data),
  });
}

// Extract and poll (combined)
export function useExtractJobDescription() {
  return useMutation({
    mutationFn: ({
      rawJd,
      employerId,
      onStatusUpdate,
    }: {
      rawJd: string;
      employerId?: string;
      onStatusUpdate?: (status: ExtractionResponse) => void;
    }) => extractionService.extractJobDescription(rawJd, employerId, onStatusUpdate),
  });
}
