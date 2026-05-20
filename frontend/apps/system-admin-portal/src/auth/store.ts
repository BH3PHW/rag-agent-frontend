import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import type { SystemUser, AuthTokens, LoginCredentials } from './types';
import { AUTH_CONFIG } from './constants';

interface AuthState {
  user: SystemUser | null;
  tokens: AuthTokens | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => Promise<void>;
  verifyToken: () => Promise<boolean>;
  refreshTokens: () => Promise<boolean>;
  clearError: () => void;
  checkAuth: () => void;
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080';

const authFetch = async <T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> => {
  const token = localStorage.getItem(AUTH_CONFIG.TOKEN_KEY);
  
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.message || `Request failed: ${response.status}`);
  }

  return response.json();
};

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      tokens: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      checkAuth: () => {
        const token = localStorage.getItem(AUTH_CONFIG.TOKEN_KEY);
        if (!token) {
          set({ isAuthenticated: false, user: null });
          return;
        }
        get().verifyToken();
      },

      login: async (credentials: LoginCredentials) => {
        set({ isLoading: true, error: null });
        
        try {
          const response = await authFetch<{
            user: SystemUser;
            token: string;
            refreshToken?: string;
          }>('/api/v1/auth/login', {
            method: 'POST',
            body: JSON.stringify(credentials),
          });

          if (response.user.role !== 'system_admin') {
            throw new Error('Access denied. System admin privileges required.');
          }

          const tokens: AuthTokens = {
            accessToken: response.token,
            refreshToken: response.refreshToken || '',
            expiresIn: 3600,
          };

          localStorage.setItem(AUTH_CONFIG.TOKEN_KEY, response.token);
          if (response.refreshToken) {
            localStorage.setItem(AUTH_CONFIG.REFRESH_TOKEN_KEY, response.refreshToken);
          }

          set({
            user: response.user,
            tokens,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Login failed',
            isLoading: false,
          });
          throw error;
        }
      },

      logout: async () => {
        try {
          await authFetch('/api/v1/auth/logout', { method: 'POST' });
        } catch {
          // Ignore logout errors
        } finally {
          localStorage.removeItem(AUTH_CONFIG.TOKEN_KEY);
          localStorage.removeItem(AUTH_CONFIG.REFRESH_TOKEN_KEY);
          set({
            user: null,
            tokens: null,
            isAuthenticated: false,
            error: null,
          });
        }
      },

      verifyToken: async () => {
        const token = localStorage.getItem(AUTH_CONFIG.TOKEN_KEY);
        if (!token) {
          set({ isAuthenticated: false, user: null });
          return false;
        }

        try {
          const response = await authFetch<SystemUser>('/api/v1/auth/me');
          
          if (response.role !== 'system_admin') {
            await get().logout();
            return false;
          }

          set({ user: response, isAuthenticated: true });
          return true;
        } catch {
          localStorage.removeItem(AUTH_CONFIG.TOKEN_KEY);
          set({ user: null, isAuthenticated: false });
          return false;
        }
      },

      refreshTokens: async () => {
        const refreshToken = localStorage.getItem(AUTH_CONFIG.REFRESH_TOKEN_KEY);
        if (!refreshToken) {
          return false;
        }

        try {
          const response = await authFetch<{ token: string }>('/api/v1/auth/refresh', {
            method: 'POST',
            body: JSON.stringify({ refreshToken }),
          });

          localStorage.setItem(AUTH_CONFIG.TOKEN_KEY, response.token);
          return true;
        } catch {
          await get().logout();
          return false;
        }
      },

      clearError: () => set({ error: null }),
    }),
    {
      name: 'sap-auth-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
      onRehydrateStorage: () => (state) => {
        if (state?.isAuthenticated) {
          state.checkAuth();
        }
      },
    }
  )
);