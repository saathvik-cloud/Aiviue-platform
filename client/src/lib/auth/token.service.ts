/**
 * JWT Token Service - Manages JWT tokens in browser storage.
 *
 * Provides utilities for:
 * - Storing access and refresh tokens
 * - Retrieving tokens for API calls
 * - Checking token expiry
 * - Clearing tokens on logout
 *
 * Uses localStorage for persistence across browser sessions.
 * Separate keys for employer and candidate tokens to allow both sessions.
 */

// Storage keys
const EMPLOYER_ACCESS_TOKEN_KEY = 'aiviue_employer_access_token';
const EMPLOYER_REFRESH_TOKEN_KEY = 'aiviue_employer_refresh_token';
const CANDIDATE_ACCESS_TOKEN_KEY = 'aiviue_candidate_access_token';
const CANDIDATE_REFRESH_TOKEN_KEY = 'aiviue_candidate_refresh_token';

// Token types
export type UserType = 'employer' | 'candidate';

export interface TokenPayload {
    sub: string;
    user_type: UserType;
    token_type: 'access' | 'refresh';
    exp: number;
    iat: number;
    employer_id?: string;
    email?: string;
    candidate_id?: string;
    mobile_number?: string;
}

export interface TokenPair {
    accessToken: string;
    refreshToken: string;
}

// ==================== TOKEN STORAGE ====================

/**
 * Check if we're running in browser environment.
 */
function isBrowser(): boolean {
    return typeof window !== 'undefined' && typeof localStorage !== 'undefined';
}

/**
 * Store tokens for a user type.
 */
export function storeTokens(userType: UserType, tokens: TokenPair): void {
    if (!isBrowser()) return;

    const accessKey =
        userType === 'employer' ? EMPLOYER_ACCESS_TOKEN_KEY : CANDIDATE_ACCESS_TOKEN_KEY;
    const refreshKey =
        userType === 'employer' ? EMPLOYER_REFRESH_TOKEN_KEY : CANDIDATE_REFRESH_TOKEN_KEY;

    localStorage.setItem(accessKey, tokens.accessToken);
    localStorage.setItem(refreshKey, tokens.refreshToken);
}

/**
 * Get access token for a user type.
 */
export function getAccessToken(userType: UserType): string | null {
    if (!isBrowser()) return null;

    const key =
        userType === 'employer' ? EMPLOYER_ACCESS_TOKEN_KEY : CANDIDATE_ACCESS_TOKEN_KEY;
    return localStorage.getItem(key);
}

/**
 * Get refresh token for a user type.
 */
export function getRefreshToken(userType: UserType): string | null {
    if (!isBrowser()) return null;

    const key =
        userType === 'employer' ? EMPLOYER_REFRESH_TOKEN_KEY : CANDIDATE_REFRESH_TOKEN_KEY;
    return localStorage.getItem(key);
}

/**
 * Clear tokens for a user type.
 */
export function clearTokens(userType: UserType): void {
    if (!isBrowser()) return;

    const accessKey =
        userType === 'employer' ? EMPLOYER_ACCESS_TOKEN_KEY : CANDIDATE_ACCESS_TOKEN_KEY;
    const refreshKey =
        userType === 'employer' ? EMPLOYER_REFRESH_TOKEN_KEY : CANDIDATE_REFRESH_TOKEN_KEY;

    localStorage.removeItem(accessKey);
    localStorage.removeItem(refreshKey);
}

/**
 * Clear all tokens (both employer and candidate).
 */
export function clearAllTokens(): void {
    if (!isBrowser()) return;

    localStorage.removeItem(EMPLOYER_ACCESS_TOKEN_KEY);
    localStorage.removeItem(EMPLOYER_REFRESH_TOKEN_KEY);
    localStorage.removeItem(CANDIDATE_ACCESS_TOKEN_KEY);
    localStorage.removeItem(CANDIDATE_REFRESH_TOKEN_KEY);
}

// ==================== TOKEN PARSING ====================

/**
 * Decode JWT payload without verification.
 * Note: This does NOT verify the signature - only use for reading claims.
 */
export function decodeToken(token: string): TokenPayload | null {
    try {
        const parts = token.split('.');
        if (parts.length !== 3) return null;

        const payload = parts[1];
        // Add padding if needed
        const padded = payload + '='.repeat((4 - (payload.length % 4)) % 4);
        const decoded = atob(padded.replace(/-/g, '+').replace(/_/g, '/'));
        return JSON.parse(decoded) as TokenPayload;
    } catch {
        return null;
    }
}

/**
 * Check if a token is expired.
 * Returns true if expired or invalid.
 * Includes a 30-second buffer to account for clock skew.
 */
export function isTokenExpired(token: string): boolean {
    const payload = decodeToken(token);
    if (!payload || !payload.exp) return true;

    const now = Math.floor(Date.now() / 1000);
    const buffer = 30; // 30 second buffer

    return payload.exp < now + buffer;
}

/**
 * Get time until token expires (in seconds).
 * Returns 0 if expired or invalid.
 */
export function getTokenExpiryTime(token: string): number {
    const payload = decodeToken(token);
    if (!payload || !payload.exp) return 0;

    const now = Math.floor(Date.now() / 1000);
    const remaining = payload.exp - now;

    return remaining > 0 ? remaining : 0;
}

/**
 * Check if access token needs refresh.
 * Returns true if token will expire within 5 minutes.
 */
export function shouldRefreshToken(token: string): boolean {
    const expiresIn = getTokenExpiryTime(token);
    const refreshThreshold = 5 * 60; // 5 minutes

    return expiresIn < refreshThreshold;
}

// ==================== TOKEN HELPERS ====================

/**
 * Get the currently active user type based on stored tokens.
 * Prefers employer if both are present.
 */
export function getActiveUserType(): UserType | null {
    const employerToken = getAccessToken('employer');
    if (employerToken && !isTokenExpired(employerToken)) {
        return 'employer';
    }

    const candidateToken = getAccessToken('candidate');
    if (candidateToken && !isTokenExpired(candidateToken)) {
        return 'candidate';
    }

    return null;
}

/**
 * Get any valid access token (prefers employer).
 */
export function getAnyValidAccessToken(): { token: string; userType: UserType } | null {
    const employerToken = getAccessToken('employer');
    if (employerToken && !isTokenExpired(employerToken)) {
        return { token: employerToken, userType: 'employer' };
    }

    const candidateToken = getAccessToken('candidate');
    if (candidateToken && !isTokenExpired(candidateToken)) {
        return { token: candidateToken, userType: 'candidate' };
    }

    return null;
}

/**
 * Check if user has a valid (non-expired) access token.
 */
export function hasValidToken(userType: UserType): boolean {
    const token = getAccessToken(userType);
    return token !== null && !isTokenExpired(token);
}
