/**
 * Candidate Chat Service - API calls + WebSocket for AIVI Resume Builder Bot.
 *
 * Dual communication:
 * - REST: Session management, history, fallback messaging
 * - WebSocket: Real-time chat during active conversation
 */

import { API_ENDPOINTS, buildQueryParams } from '@/constants';
import { del, get, post } from '@/lib/api';
import type {
    CandidateChatMessage,
    CandidateChatSessionListResponse,
    CandidateChatSessionWithMessages,
    CandidateSendMessageRequest,
    CandidateSendMessageResponse,
    CreateCandidateChatSessionRequest,
} from '@/types';

// ==================== REST API ====================

/**
 * Create a new candidate chat session.
 * Returns the session with initial welcome messages from AIVI.
 *
 * Idempotent: If an active resume session exists, returns it
 * (resume-from-where-you-left-off).
 */
export async function createCandidateChatSession(
  data: CreateCandidateChatSessionRequest
): Promise<CandidateChatSessionWithMessages> {
  return post<CandidateChatSessionWithMessages>(
    API_ENDPOINTS.CANDIDATE_CHAT.SESSIONS,
    data
  );
}

/**
 * Get list of chat sessions for a candidate (history sidebar).
 */
export async function listCandidateChatSessions(
  candidateId: string,
  limit: number = 20,
  offset: number = 0,
  activeOnly: boolean = true
): Promise<CandidateChatSessionListResponse> {
  const params = buildQueryParams({
    candidate_id: candidateId,
    limit,
    offset,
    active_only: activeOnly,
  });
  return get<CandidateChatSessionListResponse>(
    `${API_ENDPOINTS.CANDIDATE_CHAT.SESSIONS}${params}`
  );
}

/**
 * Get a single chat session with all messages.
 */
export async function getCandidateChatSession(
  sessionId: string
): Promise<CandidateChatSessionWithMessages> {
  return get<CandidateChatSessionWithMessages>(
    API_ENDPOINTS.CANDIDATE_CHAT.SESSION_BY_ID(sessionId)
  );
}

/**
 * Get the active resume session for a candidate.
 * Used for "resume from where you left off".
 * Returns 404 if no active session.
 */
export async function getActiveCandidateResumeSession(
  candidateId: string
): Promise<CandidateChatSessionWithMessages> {
  return get<CandidateChatSessionWithMessages>(
    API_ENDPOINTS.CANDIDATE_CHAT.ACTIVE_SESSION(candidateId)
  );
}

/**
 * Send a message via REST (fallback when WebSocket not available).
 */
export async function sendCandidateChatMessage(
  sessionId: string,
  data: CandidateSendMessageRequest
): Promise<CandidateSendMessageResponse> {
  return post<CandidateSendMessageResponse>(
    API_ENDPOINTS.CANDIDATE_CHAT.SESSION_MESSAGES(sessionId),
    data
  );
}

/**
 * Get messages for a session.
 */
export async function getCandidateChatMessages(
  sessionId: string,
  limit?: number
): Promise<CandidateChatMessage[]> {
  const params = limit ? buildQueryParams({ limit }) : '';
  return get<CandidateChatMessage[]>(
    `${API_ENDPOINTS.CANDIDATE_CHAT.SESSION_MESSAGES(sessionId)}${params}`
  );
}

/**
 * Delete (soft-delete) a chat session.
 */
export async function deleteCandidateChatSession(
  sessionId: string
): Promise<void> {
  return del<void>(API_ENDPOINTS.CANDIDATE_CHAT.SESSION_BY_ID(sessionId));
}

// ==================== WEBSOCKET ====================

/**
 * Build the WebSocket URL for a candidate chat session.
 * Uses API base URL so WS connects to the same backend as REST (e.g. localhost:8000 in dev).
 */
export function buildCandidateChatWSUrl(
  sessionId: string,
  candidateId: string
): string {
  const apiVersion = process.env.NEXT_PUBLIC_API_VERSION || 'v1';
  const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  const isHttps = apiBase.startsWith('https:');
  const protocol = isHttps ? 'wss:' : 'ws:';
  try {
    const url = new URL(apiBase);
    const host = url.host;
    return `${protocol}//${host}/api/${apiVersion}/candidate-chat/ws/${sessionId}?candidate_id=${candidateId}`;
  } catch {
    const host = typeof window !== 'undefined' ? window.location.host : 'localhost:8000';
    const protocol =
      typeof window !== 'undefined' && window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    return `${protocol}//${host}/api/${apiVersion}/candidate-chat/ws/${sessionId}?candidate_id=${candidateId}`;
  }
}
