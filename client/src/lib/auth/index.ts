/**
 * Auth Module - Public exports for authentication.
 *
 * Usage:
 *   import { employerLogin, getAccessToken, hasValidToken } from '@/lib/auth';
 */

// Token utilities
export {
    clearAllTokens, clearTokens, decodeToken, getAccessToken, getActiveUserType,
    getAnyValidAccessToken, getRefreshToken, getTokenExpiryTime, hasValidToken, isTokenExpired, shouldRefreshToken, storeTokens, type TokenPair, type TokenPayload, type UserType
} from './token.service';

// Auth API service
export {
    candidateLogin,
    candidateLogout, employerLogin,
    employerLogout, refreshAccessToken,
    validateToken, type CandidateLoginRequest,
    type CandidateLoginResponse, type EmployerLoginRequest,
    type EmployerLoginResponse, type TokenRefreshRequest,
    type TokenRefreshResponse,
    type TokenValidationResponse
} from './auth.service';

