/**
 * Auth Store - Zustand store for authentication state
 * 
 * Uses persist middleware to save auth state to localStorage.
 * Handles hydration properly to avoid loading loops on refresh.
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { Employer } from '@/types';

interface AuthState {
  employer: Employer | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  _hasHydrated: boolean;
  
  // Actions
  setEmployer: (employer: Employer) => void;
  clearEmployer: () => void;
  setLoading: (loading: boolean) => void;
  setHasHydrated: (state: boolean) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      employer: null,
      isAuthenticated: false,
      isLoading: true,
      _hasHydrated: false,

      setEmployer: (employer) =>
        set({
          employer,
          isAuthenticated: true,
          isLoading: false,
        }),

      clearEmployer: () =>
        set({
          employer: null,
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
          isLoading: false, // Once hydrated, we're no longer loading
        }),
    }),
    {
      name: 'aiviue-auth',
      partialize: (state) => ({
        employer: state.employer,
        isAuthenticated: state.isAuthenticated,
      }),
      onRehydrateStorage: () => (state) => {
        // Called when hydration is complete
        state?.setHasHydrated(true);
      },
    }
  )
);

// Selectors
export const selectEmployer = (state: AuthState) => state.employer;
export const selectIsAuthenticated = (state: AuthState) => state.isAuthenticated;
export const selectIsLoading = (state: AuthState) => state.isLoading;
export const selectHasHydrated = (state: AuthState) => state._hasHydrated;

export default useAuthStore;
