import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

interface User {
  id: string;
  username: string;
  email: string;
  role: string;
  enterpriseId?: string;
}

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
  clearError: () => void;
  setToken: (token: string | null) => void;
}

const API_BASE_URL = typeof window !== 'undefined' 
  ? localStorage.getItem('api-base-url') || 'http://localhost:8080' 
  : 'http://localhost:8080';

const authFetch = async <T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> => {
  const token = localStorage.getItem('auth_token');
  
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
      token: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      setToken: (token: string | null) => {
        if (token) {
          localStorage.setItem('auth_token', token);
        } else {
          localStorage.removeItem('auth_token');
        }
      },

      login: async (username: string, password: string) => {
        set({ isLoading: true, error: null });
        try {
          const result = await authFetch<{
            user: User;
            token: string;
          }>('/api/v1/auth/login', {
            method: 'POST',
            body: JSON.stringify({ username, password }),
          });

          const token = result.token;
          get().setToken(token);

          set({
            user: result.user,
            token: token,
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

      register: async (username: string, email: string, password: string) => {
        set({ isLoading: true, error: null });
        try {
          const result = await authFetch<{
            user: User;
            token: string;
          }>('/api/v1/auth/register', {
            method: 'POST',
            body: JSON.stringify({ username, email, password }),
          });

          const token = result.token;
          get().setToken(token);

          set({
            user: result.user,
            token: token,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Registration failed',
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
          get().setToken(null);
          set({
            user: null,
            token: null,
            isAuthenticated: false,
            isLoading: false,
          });
        }
      },

      checkAuth: async () => {
        const token = localStorage.getItem('auth_token');
        if (!token) {
          return;
        }
        set({ isLoading: true, error: null });
        try {
          const user = await authFetch<User>('/api/v1/auth/me');
          set({
            user: user,
            token: token,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (error) {
          get().setToken(null);
          set({
            user: null,
            token: null,
            isAuthenticated: false,
            error: error instanceof Error ? error.message : 'Authentication failed',
            isLoading: false,
          });
        }
      },

      clearError: () => set({ error: null }),
    }),
    {
      name: 'auth-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);
