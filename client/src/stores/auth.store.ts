import {
  employerLogin,
  employerLogout,
  getAccessToken,
  validateToken
} from '@/lib/auth';
import { getEmployerById } from '@/services/employer.service';
import type { Employer } from '@/types';
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface AuthState {
  employer: Employer | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  _hasHydrated: boolean;
  error: string | null;

  // Actions
  login: (email: string) => Promise<void>;
  logout: () => void;
  checkAuth: () => Promise<void>;
  setEmployer: (employer: Employer) => void;
  clearEmployer: () => void;
  setLoading: (loading: boolean) => void;
  setHasHydrated: (state: boolean) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      employer: null,
      isAuthenticated: false,
      isLoading: true,
      _hasHydrated: false,
      error: null,

      login: async (email: string) => {
        set({ isLoading: true, error: null });
        try {
          // 1. Login to get tokens
          const response = await employerLogin({ email });

          // 2. Fetch full employer profile
          const employer = await getEmployerById(response.employer_id);

          set({
            employer,
            isAuthenticated: true,
            isLoading: false
          });
        } catch (error: any) {
          console.error('Login failed:', error);
          set({
            error: error.message || 'Login failed',
            isLoading: false,
            isAuthenticated: false
          });
          throw error;
        }
      },

      logout: () => {
        employerLogout();
        set({
          employer: null,
          isAuthenticated: false,
          isLoading: false
        });
      },

      checkAuth: async () => {
        // Check if we have any token (access or refresh check handled by interceptor)
        const token = getAccessToken('employer');

        if (token) {
          try {
            // validateToken will trigger interceptor which handles refresh if needed
            const validation = await validateToken(token);

            if (validation.valid && validation.user_id) {
              // If we don't have employer data in store, fetch it
              if (!get().employer) {
                try {
                  const employer = await getEmployerById(validation.user_id);
                  set({ employer, isAuthenticated: true });
                } catch (e) {
                  console.error('Failed to fetch employer profile:', e);
                  // Keep authenticated if validation passed, even if profile fetch failed?
                  // Or maybe retry? For now, assume if validation passed, we are good.
                  // But we need employer object. 
                  // If fetch fails, maybe logout?
                  get().logout();
                }
              } else {
                set({ isAuthenticated: true });
              }
            } else {
              // Token invalid and refresh failed
              get().logout();
            }
          } catch (err) {
            // Network error or other issue
            console.error('Auth check failed:', err);
            // Don't logout immediately on network error, keep state
          }
        } else {
          // No token found
          if (get().isAuthenticated) {
            get().logout();
          }
        }
        set({ isLoading: false });
      },

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
          isLoading: false, // Once hydrated, we're no longer loading (unless a request starts)
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
        // Check auth validity on rehydration
        state?.checkAuth();
      },
    }
  )
);

// Selectors
export const selectEmployer = (state: AuthState) => state.employer;
export const selectIsAuthenticated = (state: AuthState) => state.isAuthenticated;
export const selectIsLoading = (state: AuthState) => state.isLoading;
export const selectAuthError = (state: AuthState) => state.error;
export const selectHasHydrated = (state: AuthState) => state._hasHydrated;

export default useAuthStore;
