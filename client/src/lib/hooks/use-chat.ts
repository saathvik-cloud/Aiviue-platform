/**
 * Chat Hooks - TanStack Query hooks for AIVI conversational bot.
 */

import * as chatService from '@/services/chat.service';
import type {
    CreateChatSessionRequest,
    GenerateDescriptionRequest,
    SendMessageRequest,
} from '@/types';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

// Query keys
export const chatKeys = {
    all: ['chat'] as const,
    sessions: (employerId: string) => [...chatKeys.all, 'sessions', employerId] as const,
    session: (sessionId: string) => [...chatKeys.all, 'session', sessionId] as const,
};

/**
 * Hook to fetch list of chat sessions for history sidebar.
 */
export function useChatSessions(
    employerId: string | undefined,
    limit: number = 20,
    offset: number = 0
) {
    return useQuery({
        queryKey: chatKeys.sessions(employerId || ''),
        queryFn: () => chatService.listChatSessions(employerId!, limit, offset),
        enabled: !!employerId,
    });
}

/**
 * Hook to fetch a single chat session with all messages.
 */
export function useChatSession(
    sessionId: string | undefined,
    employerId: string | undefined
) {
    return useQuery({
        queryKey: chatKeys.session(sessionId || ''),
        queryFn: () => chatService.getChatSession(sessionId!, employerId!),
        enabled: !!sessionId && !!employerId,
    });
}

/**
 * Mutation hook to create a new chat session.
 * Returns the session with welcome messages.
 */
export function useCreateChatSession() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (data: CreateChatSessionRequest) =>
            chatService.createChatSession(data),
        onSuccess: (session) => {
            // Add to sessions list cache
            queryClient.invalidateQueries({
                queryKey: chatKeys.sessions(session.employer_id),
            });
            // Set the session in cache
            queryClient.setQueryData(chatKeys.session(session.id), session);
        },
    });
}

/**
 * Mutation hook to send a message to a session.
 * Returns user message and bot responses.
 * 
 * Note: We don't invalidate the session query here to avoid duplicate messages.
 * The ChatContainer manages local state optimistically and syncs carefully.
 */
export function useSendChatMessage() {
    return useMutation({
        mutationFn: ({
            sessionId,
            employerId,
            data,
        }: {
            sessionId: string;
            employerId: string;
            data: SendMessageRequest;
        }) => chatService.sendChatMessage(sessionId, employerId, data),
        // Don't invalidate session - ChatContainer handles message state locally
        // to prevent duplicate messages from query refetch race conditions
    });
}

/**
 * Mutation hook to delete a chat session.
 */
export function useDeleteChatSession() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({
            sessionId,
            employerId,
        }: {
            sessionId: string;
            employerId: string;
        }) => chatService.deleteChatSession(sessionId, employerId),
        onSuccess: (_, { sessionId, employerId }) => {
            queryClient.removeQueries({
                queryKey: chatKeys.session(sessionId),
            });
            queryClient.invalidateQueries({
                queryKey: chatKeys.sessions(employerId),
            });
        },
    });
}

/**
 * Mutation hook to generate job description using LLM.
 * This is the ONE LLM call at the end of the conversation.
 */
export function useGenerateJobDescription() {
    return useMutation({
        mutationFn: (data: GenerateDescriptionRequest) =>
            chatService.generateJobDescription(data),
    });
}

/**
 * Mutation hook to notify backend that extraction is complete.
 * Sends extracted data and receives next steps (questions for missing fields or generate step).
 * 
 * Note: We don't invalidate the session query here to avoid duplicate messages.
 * The ChatContainer manages local state optimistically.
 */
export function useNotifyExtractionComplete() {
    return useMutation({
        mutationFn: ({
            sessionId,
            employerId,
            extractedData,
        }: {
            sessionId: string;
            employerId: string;
            extractedData: Record<string, any>;
        }) => chatService.notifyExtractionComplete(sessionId, employerId, extractedData),
        // Don't invalidate session - ChatContainer handles message state locally
        // to prevent duplicate messages from query refetch race conditions
    });
}
