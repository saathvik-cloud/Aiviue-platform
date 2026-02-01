/**
 * Extraction Types
 */

// Extraction Status
export type ExtractionStatus = 'pending' | 'processing' | 'completed' | 'failed';

// Submit Extraction Request
export interface SubmitExtractionRequest {
  raw_jd: string;
  employer_id?: string;
  idempotency_key?: string;
}

// Submit Extraction Response
export interface SubmitExtractionResponse {
  id: string;
  status: ExtractionStatus;
  message: string;
}

// Extracted Fields
export interface ExtractedFields {
  title?: string;
  description?: string;
  requirements?: string;
  location?: string;
  city?: string;
  state?: string;
  country?: string;
  work_type?: string;
  salary_range_min?: number;
  salary_range_max?: number;
  compensation?: string;
  shift_preferences?: Record<string, unknown>;
  openings_count?: number;
  extraction_confidence?: number;
  raw_extraction?: Record<string, unknown>;
}

// Extraction Response
export interface ExtractionResponse {
  id: string;
  status: ExtractionStatus;
  raw_jd_length: number;
  extracted_data?: ExtractedFields;
  error_message?: string;
  attempts: number;
  created_at: string;
  processed_at?: string;
}

// Extraction State (for wizard)
export interface ExtractionState {
  extractionId: string | null;
  status: ExtractionStatus;
  extractedData: ExtractedFields | null;
  error: string | null;
  isPolling: boolean;
}
