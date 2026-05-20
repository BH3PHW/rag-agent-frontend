import { create } from 'zustand'
import type { Agent, ChatSession, DashboardStats, ChatDetailResponse } from './types'
import { apiClient } from './api/client'

interface AppState {
  agent: Agent | null
  loading: boolean
  error: string | null
  
  stats: DashboardStats | null
  waitingChats: ChatSession[]
  myActiveChats: ChatSession[]
  currentSession: ChatDetailResponse | null
  
  setAgent: (agent: Agent | null) => void
  setError: (error: string | null) => void
  
  loadDashboard: () => Promise<void>
  loadWaitingChats: () => Promise<void>
  loadMyActiveChats: () => Promise<void>
  loadSession: (agentSessionId: string) => Promise<void>
  acceptChat: (sessionId: string) => Promise<void>
  closeChat: (sessionId: string) => Promise<void>
  sendMessage: (sessionId: string, content: string) => Promise<void>
  updateAgentStatus: (status: 'online' | 'busy' | 'offline') => Promise<void>
  logout: () => void
}

export const useAppStore = create<AppState>((set, get) => ({
  agent: null,
  loading: false,
  error: null,
  
  stats: null,
  waitingChats: [],
  myActiveChats: [],
  currentSession: null,
  
  setAgent: (agent) => set({ agent }),
  setError: (error) => set({ error }),
  
  loadDashboard: async () => {
    try {
      set({ loading: true })
      const response = await apiClient.dashboard.getStats()
      if (response.data) {
        set({ stats: response.data })
      }
    } catch (error) {
      set({ error: error instanceof Error ? error.message : '加载失败' })
    } finally {
      set({ loading: false })
    }
  },
  
  loadWaitingChats: async () => {
    try {
      set({ loading: true })
      const response = await apiClient.chats.getWaiting()
      if (response.data) {
        set({ waitingChats: response.data })
      }
    } catch (error) {
      set({ error: error instanceof Error ? error.message : '加载失败' })
    } finally {
      set({ loading: false })
    }
  },
  
  loadMyActiveChats: async () => {
    try {
      set({ loading: true })
      const response = await apiClient.chats.getMyActive()
      if (response.data) {
        set({ myActiveChats: response.data })
      }
    } catch (error) {
      set({ error: error instanceof Error ? error.message : '加载失败' })
    } finally {
      set({ loading: false })
    }
  },
  
  loadSession: async (agentSessionId: string) => {
    try {
      set({ loading: true })
      const response = await apiClient.chats.getSession(agentSessionId)
      if (response.data) {
        set({ currentSession: response.data })
      }
    } catch (error) {
      set({ error: error instanceof Error ? error.message : '加载失败' })
    } finally {
      set({ loading: false })
    }
  },
  
  acceptChat: async (sessionId: string) => {
    try {
      set({ loading: true })
      await apiClient.chats.accept(sessionId)
      await get().loadWaitingChats()
      await get().loadMyActiveChats()
    } catch (error) {
      set({ error: error instanceof Error ? error.message : '操作失败' })
    } finally {
      set({ loading: false })
    }
  },
  
  closeChat: async (sessionId: string) => {
    try {
      set({ loading: true })
      await apiClient.chats.close(sessionId)
      await get().loadMyActiveChats()
      set({ currentSession: null })
    } catch (error) {
      set({ error: error instanceof Error ? error.message : '操作失败' })
    } finally {
      set({ loading: false })
    }
  },
  
  sendMessage: async (sessionId: string, content: string) => {
    try {
      await apiClient.chats.sendMessage(sessionId, content)
      await get().loadSession(sessionId)
    } catch (error) {
      set({ error: error instanceof Error ? error.message : '发送失败' })
    }
  },
  
  updateAgentStatus: async (status) => {
    try {
      const response = await apiClient.agents.updateStatus(status)
      if (get().agent) {
        set({
          agent: {
            ...get().agent!,
            status
          }
        })
      }
    } catch (error) {
      set({ error: error instanceof Error ? error.message : '更新失败' })
    }
  },
  
  logout: () => {
    apiClient.auth.logout()
    set({
      agent: null,
      stats: null,
      waitingChats: [],
      myActiveChats: [],
      currentSession: null,
    })
  },
}))
