/**
 * API Client - Axios based HTTP client
 *
 * Authentication Strategy:
 * 1. JWT tokens (primary) - Uses Authorization: Bearer <token> header
 * 2. Legacy headers (fallback) - Uses X-Employer-Id / X-Candidate-Id for backwards compatibility
 *
 * Automatically handles:
 * - Token attachment to requests
 * - Token refresh on 401 errors
 * - Redirect to login on auth failure
 */

import { refreshAccessToken } from '@/lib/auth/auth.service';
import {
  getAccessToken,
  isTokenExpired,
  shouldRefreshToken,
} from '@/lib/auth/token.service';
import { useAuthStore } from '@/stores/auth.store';
import { useCandidateAuthStore } from '@/stores/candidate-auth.store';
import type { ApiError } from '@/types';
import axios, { AxiosError, AxiosInstance, AxiosRequestConfig, InternalAxiosRequestConfig } from 'axios';

// API Base URL
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Create axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
});

// Flag to prevent multiple simultaneous token refreshes
let isRefreshing = false;
let refreshPromise: Promise<string | null> | null = null;

// Request interceptor - adds authentication headers
apiClient.interceptors.request.use(
  async (config: InternalAxiosRequestConfig) => {
    // Add request ID
    config.headers['X-Request-ID'] = crypto.randomUUID();

    // Skip auth for auth endpoints (login, signup, etc.)
    const isAuthEndpoint = config.url?.includes('/auth/');
    if (isAuthEndpoint && !config.url?.includes('/validate')) {
      return config;
    }

    if (typeof window !== 'undefined') {
      // Try JWT token first (preferred)
      const employerToken = getAccessToken('employer');
      const candidateToken = getAccessToken('candidate');

      // Determine which token to use based on the endpoint or user context
      let token: string | null = null;
      let userType: 'employer' | 'candidate' | null = null;

      // Check for candidate-specific endpoints
      const isCandidateEndpoint =
        config.url?.includes('/candidate') ||
        config.url?.includes('/candidates');

      if (isCandidateEndpoint && candidateToken && !isTokenExpired(candidateToken)) {
        token = candidateToken;
        userType = 'candidate';
      } else if (employerToken && !isTokenExpired(employerToken)) {
        token = employerToken;
        userType = 'employer';
      } else if (candidateToken && !isTokenExpired(candidateToken)) {
        token = candidateToken;
        userType = 'candidate';
      }

      // Check if token needs refresh before request
      if (token && userType && shouldRefreshToken(token)) {
        if (!isRefreshing) {
          isRefreshing = true;
          refreshPromise = refreshAccessToken(userType);
        }

        try {
          const newToken = await refreshPromise;
          if (newToken) {
            token = newToken;
          }
        } finally {
          isRefreshing = false;
          refreshPromise = null;
        }
      }

      // Add JWT Authorization header
      if (token) {
        config.headers['Authorization'] = `Bearer ${token}`;
      }

      // Also add legacy headers for backwards compatibility
      // This ensures old endpoints still work during migration
      const employerId = useAuthStore.getState().employer?.id;
      const candidateId = useCandidateAuthStore.getState().candidate?.id;
      if (employerId) config.headers['X-Employer-Id'] = employerId;
      if (candidateId) config.headers['X-Candidate-Id'] = candidateId;
    }

    // Debug logging
    if (process.env.NEXT_PUBLIC_DEBUG_MODE === 'true') {
      console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`, config.data);
    }

    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor - handles errors and token refresh
apiClient.interceptors.response.use(
  (response) => {
    if (process.env.NEXT_PUBLIC_DEBUG_MODE === 'true') {
      console.log(`[API] ${response.status}`, response.data);
    }
    return response;
  },
  async (error: AxiosError<ApiError>) => {
    const originalRequest = error.config;

    if (process.env.NEXT_PUBLIC_DEBUG_MODE === 'true') {
      const status = error.response?.status;
      const data = error.response?.data;
      const message = error.message || 'Network error or no response';
      console.error(
        `[API Error] ${status ?? 'no status'} ${message}`,
        data ?? '(no response body)'
      );
    }

    // Handle 401 - try to refresh token once
    if (
      error.response?.status === 401 &&
      originalRequest &&
      !(originalRequest as any)._retry
    ) {
      (originalRequest as any)._retry = true;

      // Determine user type from the failed request
      const isCandidateEndpoint =
        originalRequest.url?.includes('/candidate') ||
        originalRequest.url?.includes('/candidates');

      const userType = isCandidateEndpoint ? 'candidate' : 'employer';

      // Try to refresh the token
      const newToken = await refreshAccessToken(userType);

      if (newToken) {
        // Retry with new token
        originalRequest.headers['Authorization'] = `Bearer ${newToken}`;
        return apiClient(originalRequest);
      }

      // Refresh failed - redirect to login
      if (typeof window !== 'undefined') {
        const loginPath = isCandidateEndpoint ? '/candidate/login' : '/login';
        window.location.href = loginPath;
      }
    }

    return Promise.reject(error);
  }
);

export default apiClient;

// Helper functions
export async function get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
  const response = await apiClient.get<T>(url, config);
  return response.data;
}

export async function post<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
  const response = await apiClient.post<T>(url, data, config);
  return response.data;
}

export async function put<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
  const response = await apiClient.put<T>(url, data, config);
  return response.data;
}

export async function del<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
  const response = await apiClient.delete<T>(url, config);
  return response.data;
}

// User-friendly error messages mapping
const ERROR_MESSAGES: Record<string, string> = {
  VALIDATION_ERROR: 'Please check your input and try again.',
  NOT_FOUND: 'The requested resource was not found.',
  CONFLICT: 'This resource already exists.',
  EMPLOYER_NOT_FOUND: 'Employer account not found. Please register first.',
  JOB_NOT_FOUND: 'Job not found.',
  EMAIL_ALREADY_EXISTS: 'An account with this email already exists.',
  PHONE_ALREADY_EXISTS: 'This phone number is already registered.',
  UNAUTHORIZED: 'Please log in to continue.',
  FORBIDDEN: 'You do not have permission to perform this action.',
  UPGRADE_REQUIRED:
    'To use AIVI bot to build your resume from scratch again, upgrade to Pro.',
  SESSION_NOT_ACTIVE:
    'This chat has ended. Start a new chat to continue.',
  INTERNAL_ERROR: 'Something went wrong. Please try again later.',
  // Validation specific errors
  GST_OR_PAN_REQUIRED: 'Please provide at least one of GST Number or PAN Number.',
  NAME_REQUIRED: 'Name is required and cannot be empty.',
  PHONE_REQUIRED: 'Phone number is required and cannot be empty.',
  COMPANY_NAME_REQUIRED: 'Company name is required and cannot be empty.',
};

// Parse validation error details into readable message
function parseValidationError(error: ApiError): string {
  const details = error.error?.details;
  const message = error.error?.message || '';

  // If it's a field-specific validation error, make it readable
  if (message.toLowerCase().includes('validation failed')) {
    // Extract field name from message like "body -> company_size: Value error..."
    const fieldMatch = message.match(/body\s*->\s*(\w+):/i);
    if (fieldMatch) {
      const fieldName = fieldMatch[1].replace(/_/g, ' ');

      // Check for specific validation types
      if (message.includes('must be one of')) {
        return `Invalid ${fieldName}. Please select a valid option.`;
      }
      if (message.includes('required')) {
        return `${fieldName.charAt(0).toUpperCase() + fieldName.slice(1)} is required.`;
      }
      if (message.includes('email')) {
        return 'Please enter a valid email address.';
      }

      return `Invalid ${fieldName}. Please check your input.`;
    }
  }

  return ERROR_MESSAGES.VALIDATION_ERROR;
}

// Error helpers
export function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const apiError = error.response?.data as ApiError | undefined;
    const errorCode = apiError?.error?.code;
    const errorType = apiError?.error?.type;
    const status = error.response?.status;

    // Check for known error codes first
    if (errorCode && ERROR_MESSAGES[errorCode]) {
      return ERROR_MESSAGES[errorCode];
    }

    // Handle validation errors specially
    if (errorType === 'VALIDATION_ERROR' || status === 422) {
      return parseValidationError(apiError!);
    }

    // Handle common HTTP status codes
    if (status === 404) {
      return ERROR_MESSAGES.NOT_FOUND;
    }
    if (status === 401) {
      return ERROR_MESSAGES.UNAUTHORIZED;
    }
    if (status === 403) {
      return ERROR_MESSAGES.FORBIDDEN;
    }
    if (status === 409) {
      return ERROR_MESSAGES.CONFLICT;
    }
    if (status && status >= 500) {
      return ERROR_MESSAGES.INTERNAL_ERROR;
    }

    // Fallback to API message if available and not too technical
    const apiMessage = apiError?.error?.message;
    if (apiMessage && apiMessage.length < 100 && !apiMessage.includes('body ->')) {
      return apiMessage;
    }

    return 'An error occurred. Please try again.';
  }

  if (error instanceof Error) {
    // Don't show technical error messages
    if (error.message.includes('Network Error')) {
      return 'Unable to connect to server. Please check your connection.';
    }
    if (error.message.includes('timeout')) {
      return 'Request timed out. Please try again.';
    }
  }

  return 'An unexpected error occurred.';
}

export function isApiError(error: unknown, code: string): boolean {
  if (axios.isAxiosError(error)) {
    const apiError = error.response?.data as ApiError | undefined;
    return apiError?.error?.code === code;
  }
  return false;
}

// Get raw error for debugging (only use in dev)
export function getRawErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const apiError = error.response?.data as ApiError | undefined;
    return apiError?.error?.message || error.message || 'Unknown error';
  }
  if (error instanceof Error) {
    return error.message;
  }
  return 'Unknown error';
}
