import {
  candidateLogin,
  candidateLogout,
  getAccessToken,
  refreshAccessToken,
  validateToken
} from '@/lib/auth';
import { getCandidateById } from '@/services/candidate.service';
import type { Candidate } from '@/types';
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface CandidateAuthState {
  candidate: Candidate | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  _hasHydrated: boolean;
  error: string | null;

  // Actions
  login: (mobileNumber: string) => Promise<void>;
  logout: () => void;
  checkAuth: () => Promise<void>;
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
      error: null,

      login: async (mobileNumber: string) => {
        set({ isLoading: true, error: null });
        try {
          // 1. Login to get tokens
          const response = await candidateLogin({ mobile_number: mobileNumber });

          // 2. Fetch full candidate profile
          const candidate = await getCandidateById(response.candidate_id);

          set({
            candidate,
            isAuthenticated: true,
            isLoading: false
          });
        } catch (error: any) {
          console.error('Candidate login failed:', error);
          set({
            error: error.message || 'Login failed',
            isLoading: false,
            isAuthenticated: false
          });
          throw error;
        }
      },

      logout: () => {
        candidateLogout();
        set({
          candidate: null,
          isAuthenticated: false,
          isLoading: false
        });
      },

      checkAuth: async () => {
        const token = getAccessToken('candidate');

        if (token) {
          try {
            let validation = await validateToken(token);
            if (!validation.valid) {
              const newToken = await refreshAccessToken('candidate');
              if (newToken) validation = await validateToken(newToken);
            }
            if (validation.valid && validation.user_id) {
              if (!get().candidate) {
                try {
                  const candidate = await getCandidateById(validation.user_id);
                  set({ candidate, isAuthenticated: true });
                } catch (e) {
                  console.error('Failed to fetch candidate profile:', e);
                  get().logout();
                }
              } else {
                set({ isAuthenticated: true });
              }
            } else {
              get().logout();
            }
          } catch (err) {
            console.error('Candidate auth check failed:', err);
            // On network error keep rehydrated session so refresh doesn't log user out
            if (get().candidate && get().isAuthenticated) {
              set({ isLoading: false });
              return;
            }
            get().logout();
          }
        } else {
          if (get().isAuthenticated) {
            get().logout();
          }
        }
        set({ isLoading: false });
      },

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
        state?.checkAuth();
      },
    }
  )
);

// Selectors
export const selectCandidate = (state: CandidateAuthState) => state.candidate;
export const selectCandidateIsAuthenticated = (state: CandidateAuthState) => state.isAuthenticated;
export const selectCandidateIsLoading = (state: CandidateAuthState) => state.isLoading;
export const selectCandidateError = (state: CandidateAuthState) => state.error;
export const selectCandidateHasHydrated = (state: CandidateAuthState) => state._hasHydrated;

export default useCandidateAuthStore;
