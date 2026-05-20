import type { Agent, AgentLoginResponse, ChatSession, ChatMessage, DashboardStats, ApiResponse, ChatDetailResponse } from '../types'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8006'

let authToken: string | null = localStorage.getItem('agent_token')

export const apiClient = {
  setToken: (token: string) => {
    authToken = token
    localStorage.setItem('agent_token', token)
  },
  
  clearToken: () => {
    authToken = null
    localStorage.removeItem('agent_token')
  },
  
  getToken: () => authToken,
  
  async request<T>(endpoint: string, options: RequestInit = {}): Promise<ApiResponse<T>> {
    const url = `${API_BASE_URL}${endpoint}`
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string>),
    }
    
    if (authToken) {
      headers['Authorization'] = `Bearer ${authToken}`
    }
    
    try {
      const response = await fetch(url, {
        ...options,
        headers,
      })
      
      const data = await response.json()
      
      if (!response.ok) {
        return { error: data.detail || data.message || `请求失败: ${response.status}` }
      }
      
      return { data }
    } catch (error) {
      return { error: error instanceof Error ? error.message : '网络错误' }
    }
  },
  
  auth: {
    async login(username: string, password: string) {
      const formData = new FormData()
      formData.append('username', username)
      formData.append('password', password)
      
      const response = await fetch(`${API_BASE_URL}/api/v1/agent/login`, {
        method: 'POST',
        body: formData,
      })
      
      if (!response.ok) {
        const data = await response.json()
        return { error: data.detail || '登录失败' }
      }
      
      const data: AgentLoginResponse = await response.json()
      apiClient.setToken(data.access_token)
      return { data }
    },
    
    async logout() {
      if (authToken) {
        try {
          await fetch(`${API_BASE_URL}/api/v1/agent/logout`, {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${authToken}`,
            },
          })
        } catch (e) {
          // 忽略登出请求的错误
        }
      }
      apiClient.clearToken()
      return { data: undefined }
    },
  },
  
  dashboard: {
    async getStats() {
      return apiClient.request<DashboardStats>('/api/v1/agent/dashboard/stats')
    },
  },
  
  chats: {
    async getWaiting() {
      return apiClient.request<ChatSession[]>('/api/v1/agent/chats/waiting')
    },
    
    async getMyActive() {
      return apiClient.request<ChatSession[]>('/api/v1/agent/chats/active')
    },
    
    async getSession(agentSessionId: string) {
      return apiClient.request<ChatDetailResponse>(`/api/v1/agent/chats/${agentSessionId}`)
    },
    
    async accept(sessionId: string) {
      return apiClient.request(`/api/v1/agent/chats/${sessionId}/accept`, {
        method: 'POST',
      })
    },
    
    async close(sessionId: string) {
      return apiClient.request(`/api/v1/agent/chats/${sessionId}/close`, {
        method: 'POST',
      })
    },
    
    async sendMessage(sessionId: string, content: string) {
      return apiClient.request<ChatMessage>(`/api/v1/agent/chats/${sessionId}/messages`, {
        method: 'POST',
        body: JSON.stringify({ content, message_type: 'agent' }),
      })
    },
  },
  
  agents: {
    async getMyInfo() {
      return apiClient.request<Agent>('/api/v1/agent/profile')
    },
    
    async updateStatus(status: 'online' | 'busy' | 'offline') {
      return apiClient.request('/api/v1/agent/profile/status', {
        method: 'PUT',
        body: JSON.stringify({ status }),
      })
    },
  },
}
