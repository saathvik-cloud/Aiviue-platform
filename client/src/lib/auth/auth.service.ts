/**
 * Auth API Service - Handles authentication API calls.
 *
 * Provides functions for:
 * - Employer login/logout
 * - Candidate login/logout
 * - Token refresh
 * - Token validation
 */

import apiClient from '@/lib/api/client';
import {
    clearTokens,
    getRefreshToken,
    storeTokens,
    type TokenPair,
    type UserType,
} from './token.service';

// API endpoints
const AUTH_BASE = '/api/v1/auth';

// ==================== REQUEST/RESPONSE TYPES ====================

export interface EmployerLoginRequest {
    email: string;
}

export interface EmployerLoginResponse {
    access_token: string;
    refresh_token: string;
    token_type: string;
    expires_in: number;
    employer_id: string;
    email: string;
}

export interface CandidateLoginRequest {
    mobile_number: string;
}

export interface CandidateLoginResponse {
    access_token: string;
    refresh_token: string;
    token_type: string;
    expires_in: number;
    candidate_id: string;
    mobile_number: string;
}

export interface TokenRefreshRequest {
    refresh_token: string;
}

export interface TokenRefreshResponse {
    access_token: string;
    token_type: string;
    expires_in: number;
}

export interface TokenValidationResponse {
    valid: boolean;
    user_type?: UserType;
    user_id?: string;
    email?: string;
    mobile_number?: string;
    expires_at?: string;
}

// ==================== EMPLOYER AUTH ====================

/**
 * Login as employer with email.
 * Stores tokens and returns the login response.
 */
export async function employerLogin(
    request: EmployerLoginRequest
): Promise<EmployerLoginResponse> {
    const response = await apiClient.post<EmployerLoginResponse>(
        `${AUTH_BASE}/employer/login`,
        request
    );

    // Store tokens
    storeTokens('employer', {
        accessToken: response.data.access_token,
        refreshToken: response.data.refresh_token,
    });

    return response.data;
}

/**
 * Logout employer - clears tokens.
 */
export function employerLogout(): void {
    clearTokens('employer');
}

// ==================== CANDIDATE AUTH ====================

/**
 * Login as candidate with mobile number.
 * Stores tokens and returns the login response.
 */
export async function candidateLogin(
    request: CandidateLoginRequest
): Promise<CandidateLoginResponse> {
    const response = await apiClient.post<CandidateLoginResponse>(
        `${AUTH_BASE}/candidate/login`,
        request
    );

    // Store tokens
    storeTokens('candidate', {
        accessToken: response.data.access_token,
        refreshToken: response.data.refresh_token,
    });

    return response.data;
}

/**
 * Logout candidate - clears tokens.
 */
export function candidateLogout(): void {
    clearTokens('candidate');
}

// ==================== TOKEN REFRESH ====================

/**
 * Refresh access token using refresh token.
 * Updates stored access token if successful.
 * Returns the new access token or null if refresh failed.
 */
export async function refreshAccessToken(
    userType: UserType
): Promise<string | null> {
    const refreshToken = getRefreshToken(userType);

    if (!refreshToken) {
        console.warn(`[Auth] No refresh token available for ${userType}`);
        return null;
    }

    try {
        const response = await apiClient.post<TokenRefreshResponse>(
            `${AUTH_BASE}/refresh`,
            { refresh_token: refreshToken }
        );

        // Update stored access token (keep existing refresh token)
        storeTokens(userType, {
            accessToken: response.data.access_token,
            refreshToken: refreshToken, // Keep existing refresh token
        });

        return response.data.access_token;
    } catch (error) {
        console.error(`[Auth] Failed to refresh token for ${userType}:`, error);
        // Clear tokens on refresh failure (forces re-login)
        clearTokens(userType);
        return null;
    }
}

// ==================== TOKEN VALIDATION ====================

/**
 * Validate current access token with backend.
 * Returns validation response with user info if valid.
 */
export async function validateToken(
    accessToken: string
): Promise<TokenValidationResponse> {
    try {
        const response = await apiClient.get<TokenValidationResponse>(
            `${AUTH_BASE}/validate`,
            {
                headers: {
                    Authorization: `Bearer ${accessToken}`,
                },
            }
        );
        return response.data;
    } catch {
        return { valid: false };
    }
}

// ==================== UTILITY EXPORTS ====================

export { clearAllTokens, clearTokens, storeTokens } from './token.service';
export type { TokenPair };

