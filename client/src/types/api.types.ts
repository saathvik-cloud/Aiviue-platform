/**
 * API Response Types
 */

// Base API Response
export interface ApiResponse<T> {
  data: T;
  message?: string;
}

// API Error Response
export interface ApiError {
  error: {
    type: string;
    code: string;
    message: string;
    details?: Record<string, unknown>;
    request_id?: string;
  };
}

// Pagination Response
export interface PaginatedResponse<T> {
  items: T[];
  next_cursor: string | null;
  has_more: boolean;
  total_count?: number;
}

// Pagination Params
export interface PaginationParams {
  cursor?: string;
  limit?: number;
  include_total?: boolean;
}

// Base Entity
export interface BaseEntity {
  id: string;
  created_at: string;
  updated_at: string;
  is_active: boolean;
  version: number;
}

// Health Check Response
export interface HealthCheckResponse {
  status: string;
  timestamp: string;
  environment: string;
  version: string;
  services?: {
    database?: { status: string; latency_ms?: number };
    redis?: { status: string; latency_ms?: number };
  };
}
