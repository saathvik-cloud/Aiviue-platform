/**
 * API Endpoints
 */

const API_VERSION = process.env.NEXT_PUBLIC_API_VERSION || 'v1';

export const API_ENDPOINTS = {
  // Health Check
  HEALTH: '/health',

  // Employer Endpoints (trailing slashes to avoid 307 redirects)
  EMPLOYERS: {
    BASE: `/api/${API_VERSION}/employers/`,
    BY_ID: (id: string) => `/api/${API_VERSION}/employers/${id}`,
    BY_EMAIL: (email: string) => `/api/${API_VERSION}/employers/email/${email}`,
  },

  // Job Endpoints (trailing slashes to avoid 307 redirects)
  JOBS: {
    BASE: `/api/${API_VERSION}/jobs/`,
    BY_ID: (id: string) => `/api/${API_VERSION}/jobs/${id}`,
    PUBLISH: (id: string) => `/api/${API_VERSION}/jobs/${id}/publish`,
    CLOSE: (id: string) => `/api/${API_VERSION}/jobs/${id}/close`,

    // Extraction
    EXTRACT: `/api/${API_VERSION}/jobs/extract`,
    EXTRACTION_STATUS: (id: string) => `/api/${API_VERSION}/jobs/extract/${id}`,
  },

  // Chat Endpoints (Employer)
  CHAT: {
    SESSIONS: `/api/${API_VERSION}/chat/sessions`,
    SESSION_BY_ID: (id: string) => `/api/${API_VERSION}/chat/sessions/${id}`,
    SESSION_MESSAGES: (id: string) => `/api/${API_VERSION}/chat/sessions/${id}/messages`,
    EXTRACTION_COMPLETE: (id: string) => `/api/${API_VERSION}/chat/sessions/${id}/extraction-complete`,
    GENERATE_DESCRIPTION: `/api/${API_VERSION}/chat/generate-description`,
  },

  // Candidate Endpoints
  CANDIDATES: {
    BASE: `/api/${API_VERSION}/candidates/`,
    BY_ID: (id: string) => `/api/${API_VERSION}/candidates/${id}`,
    BY_MOBILE: (mobile: string) => `/api/${API_VERSION}/candidates/mobile/${mobile}`,
    SIGNUP: `/api/${API_VERSION}/candidates/signup`,
    LOGIN: `/api/${API_VERSION}/candidates/login`,
    BASIC_PROFILE: (id: string) => `/api/${API_VERSION}/candidates/${id}/basic-profile`,
    PROFILE: (id: string) => `/api/${API_VERSION}/candidates/${id}/profile`,
    RESUME: (id: string) => `/api/${API_VERSION}/candidates/${id}/resume`,
    RESUMES: (id: string) => `/api/${API_VERSION}/candidates/${id}/resumes`,
    RESUME_BY_ID: (candidateId: string, resumeId: string) =>
      `/api/${API_VERSION}/candidates/${candidateId}/resume/${resumeId}`,
  },

  // Candidate Chat Endpoints (REST)
  CANDIDATE_CHAT: {
    SESSIONS: `/api/${API_VERSION}/candidate-chat/sessions`,
    SESSION_BY_ID: (id: string) => `/api/${API_VERSION}/candidate-chat/sessions/${id}`,
    SESSION_MESSAGES: (id: string) => `/api/${API_VERSION}/candidate-chat/sessions/${id}/messages`,
    ACTIVE_SESSION: (candidateId: string) => `/api/${API_VERSION}/candidate-chat/sessions/active/${candidateId}`,
    // WebSocket endpoint (use with new WebSocket())
    WS: (sessionId: string, candidateId: string) =>
      `${typeof window !== 'undefined' ? (window.location.protocol === 'https:' ? 'wss:' : 'ws:') : 'ws:'}//${typeof window !== 'undefined' ? window.location.host : 'localhost:8000'}/api/${API_VERSION}/candidate-chat/ws/${sessionId}?candidate_id=${candidateId}`,
  },

  // Job Master Endpoints (Categories, Roles)
  JOB_MASTER: {
    CATEGORIES: `/api/${API_VERSION}/job-master/categories`,
    CATEGORY_BY_ID: (id: string) => `/api/${API_VERSION}/job-master/categories/${id}`,
    ROLES: `/api/${API_VERSION}/job-master/roles`,
    ROLE_BY_ID: (id: string) => `/api/${API_VERSION}/job-master/roles/${id}`,
    ROLES_BY_CATEGORY: (categoryId: string) => `/api/${API_VERSION}/job-master/categories/${categoryId}/roles`,
    SEARCH_ROLES: `/api/${API_VERSION}/job-master/roles/search`,
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
