import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { api } from './api/client';
import type { User, Message, Document, CleaningRule, CleaningJob, AppSettings } from '@rag/api-client';

interface AppState {
  activePage: 'chat' | 'documents' | 'settings' | 'users' | 'cleaning' | 'sensitive';
  currentUser: User | null;
  enterpriseId: string | null;
  users: User[];
  messages: Message[];
  documents: Document[];
  cleaningRules: CleaningRule[];
  cleaningJobs: CleaningJob[];
  settings: AppSettings;
  isLoading: boolean;
  error: string | null;

  setActivePage: (page: 'chat' | 'documents' | 'settings' | 'users' | 'cleaning') => void;
  addMessage: (message: Message) => void;
  clearMessages: () => void;
  addDocument: (document: Document) => void;
  removeDocument: (id: string) => void;
  updateSettings: (settings: Partial<AppSettings>) => void;
  setIsLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;

  login: (username: string, password: string) => Promise<boolean>;
  register: (username: string, email: string, password: string) => Promise<boolean>;
  logout: () => void;
  setCurrentUser: (user: User | null) => void;
  addUser: (user: User) => void;
  removeUser: (id: string) => void;

  setCleaningRules: (rules: CleaningRule[]) => void;
  addCleaningRule: (rule: CleaningRule) => void;
  removeCleaningRule: (id: string) => void;
  updateCleaningRule: (id: string, updates: Partial<CleaningRule>) => void;
  addCleaningJob: (job: CleaningJob) => void;
  updateCleaningJob: (id: string, updates: Partial<CleaningJob>) => void;
  removeCleaningJob: (id: string) => void;

  setEnterpriseId: (id: string | null) => void;
  createEnterprise: (name: string) => Promise<boolean>;
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

const defaultCleaningRules: CleaningRule[] = [
  { id: '1', name: '移除多余空白', type: 'remove_whitespace', enabled: true },
  { id: '2', name: '移除多余换行', type: 'remove_newlines', enabled: true },
  { id: '3', name: '移除特殊字符', type: 'remove_special_chars', enabled: false },
];

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      activePage: 'chat',
      currentUser: null,
      enterpriseId: null,
      users: [],
      messages: [],
      documents: [],
      cleaningRules: defaultCleaningRules,
      cleaningJobs: [],
      settings: defaultSettings,
      isLoading: false,
      error: null,

      setActivePage: (page) => set({ activePage: page }),

      addMessage: (message) => set((state) => ({
        messages: [...state.messages, message]
      })),

      clearMessages: () => set({ messages: [] }),

      addDocument: (document) => set((state) => ({
        documents: [...state.documents, document]
      })),

      removeDocument: (id) => set((state) => ({
        documents: state.documents.filter((d) => d.id !== id)
      })),

      updateSettings: (newSettings) => set((state) => ({
        settings: { ...state.settings, ...newSettings }
      })),

      setIsLoading: (loading) => set({ isLoading: loading }),

      setError: (error) => set({ error }),

      setCurrentUser: (user) => set({ currentUser: user }),

      setEnterpriseId: (id) => set({ enterpriseId: id }),

      login: async (username: string, password: string) => {
        set({ isLoading: true, error: null });
        
        const result = await api.login({ username, password });
        
        if (result.error) {
          set({ error: result.error, isLoading: false });
          return false;
        }

        if (result.data) {
          const userResult = await api.getCurrentUser();
          if (userResult.data) {
            set({ 
              currentUser: userResult.data,
              isLoading: false 
            });
            return true;
          }
        }

        set({ error: 'Login failed', isLoading: false });
        return false;
      },

      register: async (username: string, email: string, password: string) => {
        set({ isLoading: true, error: null });
        
        const result = await api.register({ username, email, password });
        
        if (result.error) {
          set({ error: result.error, isLoading: false });
          return false;
        }

        if (result.data) {
          const userResult = await api.getCurrentUser();
          if (userResult.data) {
            set({ 
              currentUser: userResult.data,
              isLoading: false 
            });
            return true;
          }
        }

        set({ error: 'Registration failed', isLoading: false });
        return false;
      },

      logout: () => {
        api.setToken(null);
        set({ 
          currentUser: null,
          enterpriseId: null,
          messages: [],
          users: []
        });
      },

      addUser: (user) => set((state) => ({ 
        users: [...state.users, user] 
      })),

      removeUser: (id) => set((state) => ({ 
        users: state.users.filter(u => u.id !== id) 
      })),

      createEnterprise: async (name: string) => {
        set({ isLoading: true, error: null });
        
        const result = await api.createEnterprise(name);
        
        if (result.error) {
          set({ error: result.error, isLoading: false });
          return false;
        }

        if (result.data) {
          set({ 
            enterpriseId: result.data.id,
            isLoading: false 
          });
          return true;
        }

        set({ error: 'Failed to create enterprise', isLoading: false });
        return false;
      },

      setCleaningRules: (rules) => set({ cleaningRules: rules }),

      addCleaningRule: (rule) => set((state) => ({ 
        cleaningRules: [...state.cleaningRules, rule] 
      })),

      removeCleaningRule: (id) => set((state) => ({ 
        cleaningRules: state.cleaningRules.filter(r => r.id !== id) 
      })),

      updateCleaningRule: (id, updates) => set((state) => ({
        cleaningRules: state.cleaningRules.map(r => 
          r.id === id ? { ...r, ...updates } : r
        )
      })),

      addCleaningJob: (job) => set((state) => ({ 
        cleaningJobs: [...state.cleaningJobs, job] 
      })),

      updateCleaningJob: (id, updates) => set((state) => ({
        cleaningJobs: state.cleaningJobs.map(j => 
          j.id === id ? { ...j, ...updates } : j
        )
      })),

      removeCleaningJob: (id) => set((state) => ({ 
        cleaningJobs: state.cleaningJobs.filter(j => j.id !== id) 
      })),
    }),
    {
      name: 'rag-app-storage',
      partialize: (state) => ({ 
        currentUser: state.currentUser,
        enterpriseId: state.enterpriseId,
        settings: state.settings,
        cleaningRules: state.cleaningRules,
      }),
    }
  )
);
