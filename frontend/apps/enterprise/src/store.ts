import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { User, Document, CleaningRule, CleaningJob, AppSettings, Channel, ChatSession, HumanAgent, SensitiveSettings } from '@rag/api-client';

interface AppState {
  activePage: 'dashboard' | 'chat' | 'documents' | 'knowledge' | 'cleaning' | 'sensitive' | 'channels' | 'human-agent' | 'chat-monitor' | 'settings';
  currentUser: User | null;
  enterpriseId: string | null;
  users: User[];
  documents: Document[];
  cleaningRules: CleaningRule[];
  cleaningJobs: CleaningJob[];
  settings: AppSettings;
  channels: Channel[];
  chatSessions: ChatSession[];
  humanAgents: HumanAgent[];
  sensitiveSettings: SensitiveSettings;
  isLoading: boolean;
  error: string | null;

  setActivePage: (page: AppState['activePage']) => void;
  addMessage: (message: unknown) => void;
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

  setChannels: (channels: Channel[]) => void;
  addChannel: (channel: Channel) => void;
  removeChannel: (id: string) => void;
  updateChannel: (id: string, updates: Partial<Channel>) => void;

  setChatSessions: (sessions: ChatSession[]) => void;
  updateChatSession: (id: string, updates: Partial<ChatSession>) => void;

  setHumanAgents: (agents: HumanAgent[]) => void;
  addHumanAgent: (agent: HumanAgent) => void;
  removeHumanAgent: (id: string) => void;
  updateHumanAgent: (id: string, updates: Partial<HumanAgent>) => void;

  setSensitiveSettings: (settings: SensitiveSettings) => void;
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

const defaultSensitiveSettings: SensitiveSettings = {
  enable_semantic_detection: true,
  enable_keyword_detection: true,
  human_required_categories: ['money', 'political', 'religion'],
  semantic_rules: [
    { id: '1', category: 'money', description: '涉及金钱话题', keywords: ['钱', '价格', '付款'], enabled: true, requires_human: true },
    { id: '2', category: 'political', description: '涉及政治话题', keywords: ['政治', '政府'], enabled: true, requires_human: true },
  ],
  sensitivity_threshold: 0.7,
  auto_escalation_enabled: true,
  sensitive_words: [],
};

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      activePage: 'dashboard',
      currentUser: null,
      enterpriseId: null,
      users: [],
      documents: [],
      cleaningRules: defaultCleaningRules,
      cleaningJobs: [],
      settings: defaultSettings,
      channels: [],
      chatSessions: [],
      humanAgents: [],
      sensitiveSettings: defaultSensitiveSettings,
      isLoading: false,
      error: null,

      setActivePage: (page) => set({ activePage: page }),

      addMessage: () => {},

      clearMessages: () => {},

      addDocument: (document) => set((state) => ({
        documents: [...state.documents, document]
      })),

      removeDocument: (id) => set((state) => ({
        documents: state.documents.filter((d: Document) => d.id !== id)
      })),

      updateSettings: (newSettings) => set((state) => ({
        settings: { ...state.settings, ...newSettings }
      })),

      setIsLoading: (loading) => set({ isLoading: loading }),

      setError: (error) => set({ error }),

      setCurrentUser: (user) => set({ currentUser: user }),

      setEnterpriseId: (id) => set({ enterpriseId: id }),

      login: async () => {
        return false;
      },

      register: async () => {
        return false;
      },

      logout: () => set({
        currentUser: null,
        enterpriseId: null,
        users: [],
      }),

      addUser: (user) => set((state) => ({
        users: [...state.users, user]
      })),

      removeUser: (id) => set((state) => ({
        users: state.users.filter((u: User) => u.id !== id)
      })),

      createEnterprise: async () => {
        return false;
      },

      setCleaningRules: (rules) => set({ cleaningRules: rules }),

      addCleaningRule: (rule) => set((state) => ({
        cleaningRules: [...state.cleaningRules, rule]
      })),

      removeCleaningRule: (id) => set((state) => ({
        cleaningRules: state.cleaningRules.filter((r: CleaningRule) => r.id !== id)
      })),

      updateCleaningRule: (id, updates) => set((state) => ({
        cleaningRules: state.cleaningRules.map((r: CleaningRule) =>
          r.id === id ? { ...r, ...updates } : r
        )
      })),

      addCleaningJob: (job) => set((state) => ({
        cleaningJobs: [...state.cleaningJobs, job]
      })),

      updateCleaningJob: (id, updates) => set((state) => ({
        cleaningJobs: state.cleaningJobs.map((j: CleaningJob) =>
          j.id === id ? { ...j, ...updates } : j
        )
      })),

      removeCleaningJob: (id) => set((state) => ({
        cleaningJobs: state.cleaningJobs.filter((j: CleaningJob) => j.id !== id)
      })),

      setChannels: (channels) => set({ channels }),

      addChannel: (channel) => set((state) => ({
        channels: [...state.channels, channel]
      })),

      removeChannel: (id) => set((state) => ({
        channels: state.channels.filter((c: Channel) => c.id !== id)
      })),

      updateChannel: (id, updates) => set((state) => ({
        channels: state.channels.map((c: Channel) =>
          c.id === id ? { ...c, ...updates } : c
        )
      })),

      setChatSessions: (sessions) => set({ chatSessions: sessions }),

      updateChatSession: (id, updates) => set((state) => ({
        chatSessions: state.chatSessions.map((s: ChatSession) =>
          s.id === id ? { ...s, ...updates } : s
        )
      })),

      setHumanAgents: (agents) => set({ humanAgents: agents }),

      addHumanAgent: (agent) => set((state) => ({
        humanAgents: [...state.humanAgents, agent]
      })),

      removeHumanAgent: (id) => set((state) => ({
        humanAgents: state.humanAgents.filter((a: HumanAgent) => a.id !== id)
      })),

      updateHumanAgent: (id, updates) => set((state) => ({
        humanAgents: state.humanAgents.map((a: HumanAgent) =>
          a.id === id ? { ...a, ...updates } : a
        )
      })),

      setSensitiveSettings: (settings) => set({ sensitiveSettings: settings }),
    }),
    {
      name: 'rag-enterprise-storage',
      partialize: (state) => ({
        currentUser: state.currentUser,
        enterpriseId: state.enterpriseId,
        settings: state.settings,
        cleaningRules: state.cleaningRules,
        sensitiveSettings: state.sensitiveSettings,
      }),
    }
  )
);
