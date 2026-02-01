/**
 * Auth Store - Zustand store for authentication state
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { Employer } from '@/types';

interface AuthState {
  employer: Employer | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  
  // Actions
  setEmployer: (employer: Employer) => void;
  clearEmployer: () => void;
  setLoading: (loading: boolean) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      employer: null,
      isAuthenticated: false,
      isLoading: true,

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
    }),
    {
      name: 'aiviue-auth',
      partialize: (state) => ({
        employer: state.employer,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);

// Selectors
export const selectEmployer = (state: AuthState) => state.employer;
export const selectIsAuthenticated = (state: AuthState) => state.isAuthenticated;
export const selectIsLoading = (state: AuthState) => state.isLoading;

export default useAuthStore;
