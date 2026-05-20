export interface User {
  id: string
  username: string
  email: string
  role: 'agent' | 'admin' | 'system_admin'
  enterprise_id?: string
  created_at?: string
}

export interface Agent {
  id: string
  name: string
  username: string
  status: 'online' | 'busy' | 'offline'
  current_chats: number
  total_chats: number
  max_concurrent_chats: number
  enterprise_id: string
  email?: string
  phone?: string
  avatar?: string
  description?: string
  created_at: string
  updated_at: string
}

export interface AgentLoginResponse {
  access_token: string
  token_type: string
  agent: Agent
}

export interface ChatSession {
  id: string
  session_id: string
  agent_id?: string
  user_name?: string
  topic?: string
  priority: number
  enterprise_id: string
  status: 'waiting' | 'active' | 'closed'
  started_at: string
  ended_at?: string
}

export interface ChatDetailResponse {
  agent_session: {
    id: string
    session_id: string
    status: string
    user_name?: string
    topic?: string
    started_at: string
  }
  messages: ChatMessage[]
}

export interface ChatMessage {
  id?: string
  role: 'user' | 'agent' | 'assistant'
  content: string
  created_at?: string
}

export interface DashboardStats {
  active_sessions: number
  waiting_sessions: number
  total_chats_today: number
  avg_response_time: number
  satisfaction_rate: number
  online_agents: number
  total_agents: number
}

export interface ApiResponse<T = any> {
  data?: T
  error?: string
  message?: string
}
