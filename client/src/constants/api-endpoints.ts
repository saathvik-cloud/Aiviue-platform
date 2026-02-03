/**
 * API Endpoints
 */

const API_VERSION = process.env.NEXT_PUBLIC_API_VERSION || 'v1';

export const API_ENDPOINTS = {
  // Health Check
  HEALTH: '/health',

  // Employer Endpoints
  EMPLOYERS: {
    BASE: `/api/${API_VERSION}/employers`,
    BY_ID: (id: string) => `/api/${API_VERSION}/employers/${id}`,
    BY_EMAIL: (email: string) => `/api/${API_VERSION}/employers/email/${email}`,
  },

  // Job Endpoints
  JOBS: {
    BASE: `/api/${API_VERSION}/jobs`,
    BY_ID: (id: string) => `/api/${API_VERSION}/jobs/${id}`,
    PUBLISH: (id: string) => `/api/${API_VERSION}/jobs/${id}/publish`,
    CLOSE: (id: string) => `/api/${API_VERSION}/jobs/${id}/close`,

    // Extraction
    EXTRACT: `/api/${API_VERSION}/jobs/extract`,
    EXTRACTION_STATUS: (id: string) => `/api/${API_VERSION}/jobs/extract/${id}`,
  },

  // Chat Endpoints
  CHAT: {
    SESSIONS: `/api/${API_VERSION}/chat/sessions`,
    SESSION_BY_ID: (id: string) => `/api/${API_VERSION}/chat/sessions/${id}`,
    SESSION_MESSAGES: (id: string) => `/api/${API_VERSION}/chat/sessions/${id}/messages`,
    GENERATE_DESCRIPTION: `/api/${API_VERSION}/chat/generate-description`,
  },
} as const;

// Query parameter builder
export const buildQueryParams = (params: Record<string, string | number | boolean | undefined>): string => {
  const searchParams = new URLSearchParams();

  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      searchParams.append(key, String(value));
    }
  });

  const queryString = searchParams.toString();
  return queryString ? `?${queryString}` : '';
};

export default API_ENDPOINTS;
