/**
 * Candidate Auth Store - Zustand store for candidate authentication state.
 *
 * Uses persist middleware to save auth state to localStorage.
 * Separate from employer auth to allow independent sessions.
 * Handles hydration properly to avoid loading loops on refresh.
 */

import type { Candidate } from '@/types';
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface CandidateAuthState {
  candidate: Candidate | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  _hasHydrated: boolean;

  // Actions
  setCandidate: (candidate: Candidate) => void;
  updateCandidate: (updates: Partial<Candidate>) => void;
  clearCandidate: () => void;
  setLoading: (loading: boolean) => void;
  setHasHydrated: (state: boolean) => void;
}

export const useCandidateAuthStore = create<CandidateAuthState>()(
  persist(
    (set, get) => ({
      candidate: null,
      isAuthenticated: false,
      isLoading: true,
      _hasHydrated: false,

      setCandidate: (candidate) =>
        set({
          candidate,
          isAuthenticated: true,
          isLoading: false,
        }),

      updateCandidate: (updates) => {
        const current = get().candidate;
        if (current) {
          set({
            candidate: { ...current, ...updates },
          });
        }
      },

      clearCandidate: () =>
        set({
          candidate: null,
          isAuthenticated: false,
          isLoading: false,
        }),

      setLoading: (loading) =>
        set({
          isLoading: loading,
        }),

      setHasHydrated: (state) =>
        set({
          _hasHydrated: state,
          isLoading: false,
        }),
    }),
    {
      name: 'aiviue-candidate-auth',
      partialize: (state) => ({
        candidate: state.candidate,
        isAuthenticated: state.isAuthenticated,
      }),
      onRehydrateStorage: () => (state) => {
        state?.setHasHydrated(true);
      },
    }
  )
);

// Selectors
export const selectCandidate = (state: CandidateAuthState) => state.candidate;
export const selectCandidateIsAuthenticated = (state: CandidateAuthState) =>
  state.isAuthenticated;
export const selectCandidateIsLoading = (state: CandidateAuthState) =>
  state.isLoading;
export const selectCandidateHasHydrated = (state: CandidateAuthState) =>
  state._hasHydrated;

export default useCandidateAuthStore;
