const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export interface ApiResponse<T = any> {
  data?: T;
  error?: string;
  message?: string;
}

export interface User {
  id: string;
  username: string;
  email: string;
  role: 'admin' | 'user' | 'agent';
  enterprise_id?: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface Enterprise {
  id: string;
  name: string;
  api_key?: string;
  qwen_model: string;
  created_at: string;
}

export interface KnowledgeBase {
  id: string;
  name: string;
  description?: string;
  enterprise_id: string;
  document_count: number;
  chunk_count: number;
  is_active: boolean;
  created_at: string;
}

export interface Document {
  id: string;
  filename: string;
  file_size: number;
  file_type: string;
  chunk_count: number;
  status: 'processing' | 'ready' | 'error';
  created_at: string;
}

export interface ChatSession {
  id: string;
  title?: string;
  user_id: string;
  enterprise_id: string;
  message_count: number;
  is_active: boolean;
  created_at: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: SourceReference[];
  is_sensitive: boolean;
  requires_human: boolean;
  created_at: string;
}

export interface SourceReference {
  document_id?: string;
  chunk_id?: string;
  content: string;
  score: number;
}

export interface Alert {
  id: string;
  alert_type: string;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  status: 'pending' | 'acknowledged' | 'resolved';
  content?: string;
  created_at: string;
}

export interface SemanticRule {
  id?: string;
  category: string;
  description: string;
  keywords: string[];
  enabled: boolean;
  requires_human: boolean;
}

export interface SensitiveSettings {
  enable_semantic_detection: boolean;
  enable_keyword_detection: boolean;
  human_required_categories: string[];
  semantic_rules: SemanticRule[];
  sensitivity_threshold: number;
  auto_escalation_enabled: boolean;
  sensitive_words: string[];
}

class ApiClient {
  private baseUrl: string;
  private token: string | null = null;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  setToken(token: string | null) {
    this.token = token;
  }

  getToken(): string | null {
    return this.token;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (this.token) {
      (headers as Record<string, string>)['Authorization'] = `Bearer ${this.token}`;
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      const data = await response.json();

      if (!response.ok) {
        return {
          error: data.detail || 'Request failed',
        };
      }

      return { data };
    } catch (error) {
      return {
        error: error instanceof Error ? error.message : 'Network error',
      };
    }
  }

  // Auth endpoints
  async login(credentials: LoginRequest): Promise<ApiResponse<TokenResponse>> {
    const result = await this.request<TokenResponse>('/api/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });

    if (result.data?.access_token) {
      this.setToken(result.data.access_token);
    }

    return result;
  }

  async register(data: RegisterRequest): Promise<ApiResponse<TokenResponse>> {
    const result = await this.request<TokenResponse>('/api/v1/auth/register', {
      method: 'POST',
      body: JSON.stringify(data),
    });

    if (result.data?.access_token) {
      this.setToken(result.data.access_token);
    }

    return result;
  }

  async getCurrentUser(): Promise<ApiResponse<User>> {
    return this.request<User>('/api/v1/auth/me');
  }

  // Enterprise endpoints
  async createEnterprise(name: string): Promise<ApiResponse<Enterprise>> {
    return this.request<Enterprise>('/api/v1/enterprises', {
      method: 'POST',
      body: JSON.stringify({ name }),
    });
  }

  async getEnterprise(enterpriseId: string): Promise<ApiResponse<Enterprise>> {
    return this.request<Enterprise>(`/api/v1/enterprises/${enterpriseId}`);
  }

  // Knowledge base endpoints
  async createKnowledgeBase(
    name: string,
    enterpriseId: string,
    description?: string
  ): Promise<ApiResponse<KnowledgeBase>> {
    return this.request<KnowledgeBase>('/api/v1/knowledge-bases', {
      method: 'POST',
      body: JSON.stringify({ name, enterprise_id: enterpriseId, description }),
    });
  }

  async getKnowledgeBases(enterpriseId: string): Promise<ApiResponse<KnowledgeBase[]>> {
    return this.request<KnowledgeBase[]>(
      `/api/v1/knowledge-bases?enterprise_id=${enterpriseId}`
    );
  }

  async uploadDocument(
    knowledgeBaseId: string,
    enterpriseId: string,
    file: File
  ): Promise<ApiResponse<{ document_id: string; filename: string; status: string }>> {
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(
        `${this.baseUrl}/api/v1/knowledge-bases/${knowledgeBaseId}/documents?enterprise_id=${enterpriseId}`,
        {
          method: 'POST',
          headers: this.token ? { Authorization: `Bearer ${this.token}` } : {},
          body: formData,
        }
      );

      const data = await response.json();

      if (!response.ok) {
        return { error: data.detail || 'Upload failed' };
      }

      return { data };
    } catch (error) {
      return {
        error: error instanceof Error ? error.message : 'Upload error',
      };
    }
  }

  async getDocuments(
    knowledgeBaseId: string,
    enterpriseId: string
  ): Promise<ApiResponse<Document[]>> {
    return this.request<Document[]>(
      `/api/v1/knowledge-bases/${knowledgeBaseId}/documents?enterprise_id=${enterpriseId}`
    );
  }

  async deleteDocument(documentId: string, enterpriseId: string): Promise<ApiResponse<void>> {
    return this.request<void>(
      `/api/v1/documents/${documentId}?enterprise_id=${enterpriseId}`,
      { method: 'DELETE' }
    );
  }

  // Chat endpoints
  async createChatSession(
    userId: string,
    enterpriseId: string,
    title?: string
  ): Promise<ApiResponse<ChatSession>> {
    return this.request<ChatSession>('/api/v1/chat/sessions', {
      method: 'POST',
      body: JSON.stringify({ user_id: userId, enterprise_id: enterpriseId, title }),
    });
  }

  async getChatSessions(
    userId: string,
    enterpriseId: string
  ): Promise<ApiResponse<ChatSession[]>> {
    return this.request<ChatSession[]>(
      `/api/v1/chat/sessions?user_id=${userId}&enterprise_id=${enterpriseId}`
    );
  }

  async sendMessage(
    sessionId: string,
    userId: string,
    content: string
  ): Promise<ApiResponse<{
    message_id: string;
    role: string;
    content: string;
    sources: SourceReference[];
    is_sensitive: boolean;
    requires_human: boolean;
  }>> {
    return this.request(`/api/v1/chat/sessions/${sessionId}/messages`, {
      method: 'POST',
      body: JSON.stringify({ content, user_id: userId }),
    });
  }

  async getMessages(
    sessionId: string,
    userId: string
  ): Promise<ApiResponse<ChatMessage[]>> {
    return this.request<ChatMessage[]>(
      `/api/v1/chat/sessions/${sessionId}/messages?user_id=${userId}`
    );
  }

  async deleteSession(sessionId: string, userId: string): Promise<ApiResponse<void>> {
    return this.request<void>(
      `/api/v1/chat/sessions/${sessionId}?user_id=${userId}`,
      { method: 'DELETE' }
    );
  }

  // Alert endpoints
  async getAlerts(enterpriseId: string): Promise<ApiResponse<Alert[]>> {
    return this.request<Alert[]>(`/api/v1/alerts?enterprise_id=${enterpriseId}`);
  }

  async acknowledgeAlert(alertId: string): Promise<ApiResponse<void>> {
    return this.request<void>(`/api/v1/alerts/${alertId}/acknowledge`, {
      method: 'PUT',
    });
  }

  async resolveAlert(
    alertId: string,
    resolutionNotes?: string
  ): Promise<ApiResponse<void>> {
    return this.request<void>(`/api/v1/alerts/${alertId}/resolve`, {
      method: 'PUT',
      body: JSON.stringify({ resolution_notes: resolutionNotes }),
    });
  }

  async getAlertStats(enterpriseId: string): Promise<ApiResponse<{
    total: number;
    pending: number;
    acknowledged: number;
    resolved: number;
  }>> {
    return this.request(`/api/v1/alerts/stats?enterprise_id=${enterpriseId}`);
  }

  // Sensitive settings endpoints
  async getSensitiveSettings(enterpriseId: string): Promise<ApiResponse<SensitiveSettings>> {
    return this.request<SensitiveSettings>(`/api/v1/enterprises/${enterpriseId}/sensitive-settings`);
  }

  async updateSensitiveSettings(
    enterpriseId: string,
    settings: SensitiveSettings
  ): Promise<ApiResponse<SensitiveSettings>> {
    return this.request<SensitiveSettings>(`/api/v1/enterprises/${enterpriseId}/sensitive-settings`, {
      method: 'PUT',
      body: JSON.stringify(settings),
    });
  }

  async updateSensitiveWords(
    enterpriseId: string,
    sensitiveWords: string[]
  ): Promise<ApiResponse<SensitiveSettings>> {
    return this.request<SensitiveSettings>(`/api/v1/enterprises/${enterpriseId}/sensitive-words`, {
      method: 'PUT',
      body: JSON.stringify({ sensitive_words: sensitiveWords }),
    });
  }

  async createSemanticRule(
    enterpriseId: string,
    rule: Omit<SemanticRule, 'id'>
  ): Promise<ApiResponse<SemanticRule>> {
    return this.request<SemanticRule>(`/api/v1/enterprises/${enterpriseId}/semantic-rules`, {
      method: 'POST',
      body: JSON.stringify(rule),
    });
  }

  async deleteSemanticRule(
    enterpriseId: string,
    ruleId: string
  ): Promise<ApiResponse<void>> {
    return this.request<void>(`/api/v1/enterprises/${enterpriseId}/semantic-rules/${ruleId}`, {
      method: 'DELETE',
    });
  }
}

export const api = new ApiClient(API_BASE_URL);
export default api;
