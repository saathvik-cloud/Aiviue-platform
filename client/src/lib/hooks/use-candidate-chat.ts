/**
 * Candidate Chat Hooks - TanStack Query hooks for AIVI Resume Builder Bot.
 *
 * Follows the same pattern as employer chat hooks (use-chat.ts).
 * Separate from employer chat to maintain clean domain boundaries.
 */

import * as candidateChatService from '@/services/candidate-chat.service';
import type {
  CandidateSendMessageRequest,
  CreateCandidateChatSessionRequest,
} from '@/types';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

// ==================== QUERY KEYS ====================

export const candidateChatKeys = {
  all: ['candidateChat'] as const,
  sessions: (candidateId: string) =>
    [...candidateChatKeys.all, 'sessions', candidateId] as const,
  session: (sessionId: string) =>
    [...candidateChatKeys.all, 'session', sessionId] as const,
  activeSession: (candidateId: string) =>
    [...candidateChatKeys.all, 'activeSession', candidateId] as const,
};

// ==================== SESSION QUERIES ====================

/**
 * Hook to fetch list of chat sessions for history sidebar.
 * 
 * PERF: Pass enabled=false to defer fetching until user opens history panel.
 */
export function useCandidateChatSessions(
  candidateId: string | undefined,
  limit: number = 20,
  offset: number = 0,
  enabled: boolean = true
) {
  return useQuery({
    queryKey: candidateChatKeys.sessions(candidateId || ''),
    queryFn: () =>
      candidateChatService.listCandidateChatSessions(candidateId!, limit, offset),
    enabled: enabled && !!candidateId,
    staleTime: 30000, // Don't refetch for 30 seconds (history doesn't change often)
  });
}

/**
 * Hook to fetch a single chat session with all messages.
 */
export function useCandidateChatSession(sessionId: string | undefined) {
  return useQuery({
    queryKey: candidateChatKeys.session(sessionId || ''),
    queryFn: () => candidateChatService.getCandidateChatSession(sessionId!),
    enabled: !!sessionId,
  });
}

/**
 * Hook to fetch the active resume session (resume-from-where-you-left-off).
 */
export function useActiveCandidateResumeSession(
  candidateId: string | undefined
) {
  return useQuery({
    queryKey: candidateChatKeys.activeSession(candidateId || ''),
    queryFn: () =>
      candidateChatService.getActiveCandidateResumeSession(candidateId!),
    enabled: !!candidateId,
    retry: false, // Don't retry on 404 (no active session is normal)
  });
}

// ==================== SESSION MUTATIONS ====================

/**
 * Mutation hook to create a new chat session.
 * Returns the session with welcome messages.
 *
 * Idempotent: backend returns existing active session if found.
 */
export function useCreateCandidateChatSession() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateCandidateChatSessionRequest) =>
      candidateChatService.createCandidateChatSession(data),
    onSuccess: (session) => {
      // Add to sessions list cache
      queryClient.invalidateQueries({
        queryKey: candidateChatKeys.sessions(session.candidate_id),
      });
      // Set the session in cache
      queryClient.setQueryData(
        candidateChatKeys.session(session.id),
        session
      );
      // Invalidate active session cache
      queryClient.invalidateQueries({
        queryKey: candidateChatKeys.activeSession(session.candidate_id),
      });
    },
  });
}

/**
 * Mutation hook to send a message via REST (POST /sessions/:id/messages).
 *
 * Don't invalidate session query to avoid duplicate messages.
 * The chat component manages local state optimistically.
 */
export function useSendCandidateChatMessage() {
  return useMutation({
    mutationFn: ({
      sessionId,
      data,
    }: {
      sessionId: string;
      data: CandidateSendMessageRequest;
    }) => candidateChatService.sendCandidateChatMessage(sessionId, data),
  });
}

/**
 * Mutation hook to delete a chat session.
 */
export function useDeleteCandidateChatSession() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      sessionId,
      candidateId,
    }: {
      sessionId: string;
      candidateId: string;
    }) => candidateChatService.deleteCandidateChatSession(sessionId),
    onSuccess: (_, { sessionId, candidateId }) => {
      queryClient.removeQueries({
        queryKey: candidateChatKeys.session(sessionId),
      });
      queryClient.invalidateQueries({
        queryKey: candidateChatKeys.sessions(candidateId),
      });
    },
  });
}
