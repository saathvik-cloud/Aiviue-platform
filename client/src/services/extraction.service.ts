/**
 * Extraction Service - API calls for JD extraction
 */

import { get, post } from '@/lib/api';
import { API_ENDPOINTS, EXTRACTION_POLL_INTERVAL, EXTRACTION_MAX_POLLS } from '@/constants';
import { sleep } from '@/lib/utils';
import type {
  SubmitExtractionRequest,
  SubmitExtractionResponse,
  ExtractionResponse,
} from '@/types';

// Submit extraction
export async function submitExtraction(data: SubmitExtractionRequest): Promise<SubmitExtractionResponse> {
  return post<SubmitExtractionResponse>(API_ENDPOINTS.JOBS.EXTRACT, data);
}

// Get extraction status
export async function getExtractionStatus(id: string): Promise<ExtractionResponse> {
  return get<ExtractionResponse>(API_ENDPOINTS.JOBS.EXTRACTION_STATUS(id));
}

// Poll extraction until complete
export async function pollExtraction(
  id: string,
  onStatusUpdate?: (status: ExtractionResponse) => void
): Promise<ExtractionResponse> {
  let attempts = 0;

  while (attempts < EXTRACTION_MAX_POLLS) {
    const result = await getExtractionStatus(id);
    
    // Notify status update
    if (onStatusUpdate) {
      onStatusUpdate(result);
    }

    // Check if done
    if (result.status === 'completed' || result.status === 'failed') {
      return result;
    }

    // Wait before next poll
    await sleep(EXTRACTION_POLL_INTERVAL);
    attempts++;
  }

  throw new Error('Extraction timed out');
}

// Submit and wait for extraction (combined)
export async function extractJobDescription(
  rawJd: string,
  employerId?: string,
  onStatusUpdate?: (status: ExtractionResponse) => void
): Promise<ExtractionResponse> {
  // Submit
  const submission = await submitExtraction({
    raw_jd: rawJd,
    employer_id: employerId,
  });

  // Poll until complete
  return pollExtraction(submission.id, onStatusUpdate);
}
