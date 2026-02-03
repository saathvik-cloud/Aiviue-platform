/**
 * Chat Service - API calls for AIVI conversational bot.
 */

import { API_ENDPOINTS, buildQueryParams } from '@/constants';
import { del, get, post } from '@/lib/api';
import type {
    ChatSessionListResponse,
    ChatSessionWithMessages,
    CreateChatSessionRequest,
    GenerateDescriptionRequest,
    GenerateDescriptionResponse,
    SendMessageRequest,
    SendMessageResponse
} from '@/types';

/**
 * Create a new chat session.
 * Returns the session with initial welcome messages from AIVI.
 */
export async function createChatSession(
    data: CreateChatSessionRequest
): Promise<ChatSessionWithMessages> {
    return post<ChatSessionWithMessages>(API_ENDPOINTS.CHAT.SESSIONS, data);
}

/**
 * Get list of chat sessions for an employer.
 * Supports pagination with limit and offset.
 */
export async function listChatSessions(
    employerId: string,
    limit: number = 20,
    offset: number = 0
): Promise<ChatSessionListResponse> {
    const params = buildQueryParams({
        employer_id: employerId,
        limit,
        offset,
    });
    return get<ChatSessionListResponse>(`${API_ENDPOINTS.CHAT.SESSIONS}${params}`);
}

/**
 * Get a single chat session with all its messages.
 */
export async function getChatSession(
    sessionId: string,
    employerId: string
): Promise<ChatSessionWithMessages> {
    const params = buildQueryParams({ employer_id: employerId });
    return get<ChatSessionWithMessages>(
        `${API_ENDPOINTS.CHAT.SESSION_BY_ID(sessionId)}${params}`
    );
}

/**
 * Delete a chat session.
 */
export async function deleteChatSession(
    sessionId: string,
    employerId: string
): Promise<void> {
    const params = buildQueryParams({ employer_id: employerId });
    return del<void>(`${API_ENDPOINTS.CHAT.SESSION_BY_ID(sessionId)}${params}`);
}

/**
 * Send a message to a chat session.
 * Returns the user message and bot responses.
 */
export async function sendChatMessage(
    sessionId: string,
    employerId: string,
    data: SendMessageRequest
): Promise<SendMessageResponse> {
    const params = buildQueryParams({ employer_id: employerId });
    return post<SendMessageResponse>(
        `${API_ENDPOINTS.CHAT.SESSION_MESSAGES(sessionId)}${params}`,
        data
    );
}

/**
 * Generate job description from structured data.
 * This is the ONE LLM call at the end of the conversation.
 */
export async function generateJobDescription(
    data: GenerateDescriptionRequest
): Promise<GenerateDescriptionResponse> {
    return post<GenerateDescriptionResponse>(
        API_ENDPOINTS.CHAT.GENERATE_DESCRIPTION,
        data
    );
}
