import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface AppSettings {
  apiKey: string;
  apiEndpoint: string;
  model: string;
  temperature: number;
  topP: number;
  topK: number;
  chunkSize: number;
  chunkOverlap: number;
}

interface User {
  id: string;
  username: string;
  email: string;
  role: string;
  enterpriseId?: string;
}

interface AppState {
  settings: AppSettings;
  updateSettings: (settings: Partial<AppSettings>) => void;
  currentUser: User | null;
  enterpriseId: string | null;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<boolean>;
  register: (username: string, email: string, password: string) => Promise<boolean>;
  logout: () => void;
  createEnterprise: (name: string) => Promise<boolean>;
  error: string | null;
  setError: (error: string | null) => void;
}

const defaultSettings: AppSettings = {
  apiKey: '',
  apiEndpoint: 'https://api.openai.com/v1',
  model: 'gpt-3.5-turbo',
  temperature: 0.7,
  topP: 0.9,
  topK: 5,
  chunkSize: 1000,
  chunkOverlap: 200,
};

export const useAppStore = create<AppState>()(
  persist(
    (set, get) => ({
      settings: defaultSettings,
      updateSettings: (newSettings) =>
        set((state) => ({
          settings: { ...state.settings, ...newSettings },
        })),

      currentUser: null,
      enterpriseId: null,
      isLoading: false,
      error: null,

      setError: (error) => set({ error }),

      login: async (username, password) => {
        set({ error: null, isLoading: true });
        try {
          const response = await fetch('/api/v1/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password }),
          });

          set({ isLoading: false });

          if (!response.ok) {
            const data = await response.json();
            set({ error: data.message || '登录失败' });
            return false;
          }

          const data = await response.json();
          set({
            currentUser: data.user,
            enterpriseId: data.user.enterpriseId,
          });
          return true;
        } catch {
          set({ isLoading: false, error: '登录失败' });
          return false;
        }
      },

      register: async (username, email, password) => {
        set({ error: null, isLoading: true });
        try {
          const response = await fetch('/api/v1/auth/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, email, password }),
          });

          set({ isLoading: false });

          if (!response.ok) {
            const data = await response.json();
            set({ error: data.message || '注册失败' });
            return false;
          }

          const data = await response.json();
          set({
            currentUser: data.user,
            enterpriseId: data.user.enterpriseId,
          });
          return true;
        } catch {
          set({ isLoading: false, error: '注册失败' });
          return false;
        }
      },

      logout: () => {
        set({ currentUser: null, enterpriseId: null });
      },

      createEnterprise: async (name) => {
        set({ error: null, isLoading: true });
        const { currentUser } = get();
        
        if (!currentUser) {
          set({ error: '请先登录', isLoading: false });
          return false;
        }

        try {
          const response = await fetch('/api/v1/enterprises', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${localStorage.getItem('token')}`,
            },
            body: JSON.stringify({ name, ownerId: currentUser.id }),
          });

          set({ isLoading: false });

          if (!response.ok) {
            const data = await response.json();
            set({ error: data.message || '创建企业失败' });
            return false;
          }

          const data = await response.json();
          set({ enterpriseId: data.id });
          return true;
        } catch {
          set({ error: '创建企业失败', isLoading: false });
          return false;
        }
      },
    }),
    {
      name: 'rag-system-admin-storage',
      partialize: (state) => ({ settings: state.settings }),
    }
  )
);
