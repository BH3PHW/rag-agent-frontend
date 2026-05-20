import type { SemanticRule, SensitiveSettings } from '@rag/api-client';

interface ApiResponse<T> {
  data?: T;
  error?: string;
}

export interface User {
  id: string;
  username: string;
  email: string;
  role: string;
  createdAt?: string;
  enterpriseId?: string;
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

export interface Enterprise {
  id: string;
  name: string;
  createdAt?: string;
  updatedAt?: string;
  userCount?: number;
  documentCount?: number;
  sessionCount?: number;
}

export interface KnowledgeBase {
  id: string;
  name: string;
  description?: string;
  documents?: unknown[];
  documentCount?: number;
  enterpriseId?: string;
  createdAt?: string;
  updatedAt?: string;
}

export interface Document {
  id: string;
  filename: string;
  status: string;
  createdAt?: string;
  fileSize?: number;
  knowledgeBaseId?: string;
  enterpriseId?: string;
}

export interface ChatSession {
  id: string;
  userId: string;
  enterpriseId?: string;
  createdAt: string;
  messageCount?: number;
  title?: string;
}

export interface Alert {
  id: string;
  type: 'security' | 'system' | 'usage';
  level: 'info' | 'warning' | 'critical';
  message: string;
  status: 'active' | 'acknowledged' | 'resolved';
  createdAt: string;
  acknowledgedAt?: string;
  resolvedAt?: string;
  acknowledgedBy?: string;
  resolvedBy?: string;
  enterpriseId?: string;
}

export interface AnalyticsStats {
  totalSessions: number;
  totalMessages: number;
  totalUsers: number;
  totalDocuments: number;
  dailyActivity: Array<{ date: string; sessions: number; messages: number }>;
  topEnterprises?: Array<{ name: string; sessions: number; users: number }>;
  modelUsage?: Array<{ model: string; count: number }>;
}

export interface ServiceStatus {
  name: string;
  status: 'healthy' | 'degraded' | 'down';
  uptime: string;
  version: string;
  lastUpdate: string;
}

const DEFAULT_BASE_URL = 'http://localhost:8000';
let authToken: string | null = null;

const getBaseUrl = (): string => {
  if (typeof window !== 'undefined') {
    try {
      const stored = localStorage.getItem('rag-api-settings');
      if (stored) {
        const settings = JSON.parse(stored);
        const defaultConfig = settings.configs?.find((c: { id: string }) => c.id === settings.defaultConfig);
        return defaultConfig?.baseUrl || DEFAULT_BASE_URL;
      }
    } catch {}
  }
  return DEFAULT_BASE_URL;
};

interface EcommercePlatform {
  platform_id: string;
  name: string;
  icon: string;
  enabled: boolean;
  has_config: boolean;
  api_config: Record<string, string>;
  sync_config: Record<string, string>;
}

interface EcommerceTool {
  tool_name: string;
  name: string;
  description: string;
  category: string;
  enabled: boolean;
  config: Record<string, any>;
}

interface ApiClient {
  setToken: (token: string | null) => void;
  getToken: () => string | null;
  getBaseUrl: () => string;
  request: <T>(endpoint: string, options?: RequestInit) => Promise<ApiResponse<T>>;
  auth: {
    login: (data: LoginRequest) => Promise<ApiResponse<{ user: User; token: string }>>;
    register: (data: RegisterRequest) => Promise<ApiResponse<{ user: User; token: string }>>;
    logout: () => Promise<ApiResponse<void>>;
    getCurrentUser: () => Promise<ApiResponse<User>>;
  };
  ecommerce: {
    getPlatforms: (enterpriseId: string) => Promise<ApiResponse<EcommercePlatform[]>>;
    updatePlatform: (
      platformId: string,
      enterpriseId: string,
      enabled: boolean,
      apiConfig?: Record<string, string>,
      syncConfig?: Record<string, string>
    ) => Promise<ApiResponse<{ platform_id: string; enabled: boolean }>>;
    getTools: (enterpriseId: string) => Promise<ApiResponse<EcommerceTool[]>>;
    updateTool: (
      toolName: string,
      enterpriseId: string,
      enabled: boolean,
      config?: Record<string, any>
    ) => Promise<ApiResponse<{ tool_name: string; enabled: boolean }>>;
    getPlatformRegistry: () => Promise<ApiResponse<EcommercePlatform[]>>;
    addPlatform: (
      platformId: string,
      name: string,
      icon: string,
      apiType: string,
      configSchema?: Record<string, any>
    ) => Promise<ApiResponse<{ platform_id: string; name: string; icon: string }>>;
  };
  chat: {
    send: (message: string, enterpriseId?: string) => Promise<ApiResponse<{ content: string; sources?: unknown[] }>>;
    sendSSE: (
      message: string,
      enterpriseId: string,
      onChunk: (chunk: string) => void,
      onEnd: () => void,
      onError: (error: string) => void
    ) => Promise<void>;
    getSessions: (enterpriseId?: string, userId?: string) => Promise<ApiResponse<{ sessions: ChatSession[] }>>;
    deleteSession: (sessionId: string, userId?: string) => Promise<ApiResponse<void>>;
  };
  documents: {
    list: () => Promise<ApiResponse<{ documents: Document[] }>>;
    getDocuments: (kbId: string, enterpriseId: string) => Promise<ApiResponse<{ documents: Document[] }>>;
    getKnowledgeBases: (enterpriseId: string) => Promise<ApiResponse<{ knowledge_bases: KnowledgeBase[] }>>;
    createKnowledgeBase: (name: string, enterpriseId: string) => Promise<ApiResponse<KnowledgeBase>>;
    upload: (file: File) => Promise<ApiResponse<unknown>>;
    uploadDocument: (kbId: string, enterpriseId: string, file: File) => Promise<ApiResponse<{ document_id: string; filename: string; status: string }>>;
    delete: (id: string) => Promise<ApiResponse<void>>;
    deleteDocument: (docId: string, enterpriseId: string) => Promise<ApiResponse<void>>;
  };
  sensitive: {
    getSettings: () => Promise<ApiResponse<SensitiveSettings>>;
    getSensitiveSettings: (enterpriseId: string) => Promise<ApiResponse<SensitiveSettings>>;
    updateSettings: (settings: SensitiveSettings) => Promise<ApiResponse<SensitiveSettings>>;
    updateSensitiveSettings: (enterpriseId: string, settings: SensitiveSettings) => Promise<ApiResponse<SensitiveSettings>>;
    createSemanticRule: (rule: Omit<SemanticRule, 'id'>) => Promise<ApiResponse<SemanticRule>>;
    deleteSemanticRule: (id: string) => Promise<ApiResponse<void>>;
  };
  enterprises: {
    create: (name: string) => Promise<ApiResponse<{ id: string }>>;
    get: (id: string) => Promise<ApiResponse<Enterprise>>;
    list: () => Promise<ApiResponse<{ enterprises: Enterprise[] }>>;
    update: (id: string, data: Partial<Enterprise>) => Promise<ApiResponse<Enterprise>>;
    delete: (id: string) => Promise<ApiResponse<void>>;
    getStats: (id: string) => Promise<ApiResponse<{ userCount: number; documentCount: number; sessionCount: number }>>;
  };
  admin: {
    users: {
      list: (enterpriseId?: string) => Promise<ApiResponse<{ users: User[] }>>;
      get: (userId: string) => Promise<ApiResponse<User>>;
      create: (data: Omit<User, 'id'>) => Promise<ApiResponse<User>>;
      update: (userId: string, data: Partial<User>) => Promise<ApiResponse<User>>;
      delete: (userId: string) => Promise<ApiResponse<void>>;
    };
    alerts: {
      list: (status?: string, level?: string, enterpriseId?: string) => Promise<ApiResponse<{ alerts: Alert[] }>>;
      get: (alertId: string) => Promise<ApiResponse<Alert>>;
      acknowledge: (alertId: string) => Promise<ApiResponse<void>>;
      resolve: (alertId: string) => Promise<ApiResponse<void>>;
      delete: (alertId: string) => Promise<ApiResponse<void>>;
    };
    analytics: {
      getStats: (enterpriseId?: string) => Promise<ApiResponse<AnalyticsStats>>;
      getEnterpriseStats: (enterpriseId: string) => Promise<ApiResponse<AnalyticsStats>>;
    };
    services: {
      list: () => Promise<ApiResponse<{ services: ServiceStatus[] }>>;
    };
  };
}

const createApiRequest = async <T>(endpoint: string, options: RequestInit = {}): Promise<ApiResponse<T>> => {
  const baseUrl = getBaseUrl();
  const url = `${baseUrl}${endpoint}`;

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };

  if (authToken) {
    headers['Authorization'] = `Bearer ${authToken}`;
  }

  try {
    const response = await fetch(url, {
      ...options,
      headers,
    });

    const data = await response.json();

    if (!response.ok) {
      return { error: data.message || `Request failed: ${response.status}` };
    }

    return { data };
  } catch (error) {
    return { error: error instanceof Error ? error.message : 'Network error' };
  }
};

export const api: ApiClient = {
  setToken: (token: string | null) => {
    authToken = token;
  },

  getToken: () => authToken,

  getBaseUrl,

  request: createApiRequest,

  ecommerce: {
    getPlatforms: async (enterpriseId: string) => {
      return createApiRequest<EcommercePlatform[]>(
        `/api/v1/ecommerce/platforms?enterprise_id=${enterpriseId}`
      );
    },

    updatePlatform: async (
      platformId: string,
      enterpriseId: string,
      enabled: boolean,
      apiConfig?: Record<string, string>,
      syncConfig?: Record<string, string>
    ) => {
      return createApiRequest<{ platform_id: string; enabled: boolean }>(
        `/api/v1/ecommerce/platforms/${platformId}`,
        {
          method: 'PUT',
          body: JSON.stringify({
            enterprise_id: enterpriseId,
            enabled,
            api_config: apiConfig,
            sync_config: syncConfig,
          }),
        }
      );
    },

    getTools: async (enterpriseId: string) => {
      return createApiRequest<EcommerceTool[]>(
        `/api/v1/ecommerce/tools?enterprise_id=${enterpriseId}`
      );
    },

    updateTool: async (
      toolName: string,
      enterpriseId: string,
      enabled: boolean,
      config?: Record<string, any>
    ) => {
      return createApiRequest<{ tool_name: string; enabled: boolean }>(
        `/api/v1/ecommerce/tools/${toolName}`,
        {
          method: 'PUT',
          body: JSON.stringify({
            enterprise_id: enterpriseId,
            enabled,
            config,
          }),
        }
      );
    },

    getPlatformRegistry: async () => {
      return createApiRequest<EcommercePlatform[]>(
        `/api/v1/ecommerce/registry/platforms`
      );
    },

    addPlatform: async (
      platformId: string,
      name: string,
      icon: string,
      apiType: string,
      configSchema?: Record<string, any>
    ) => {
      const params = new URLSearchParams({
        platform_id: platformId,
        name: name,
        icon: icon,
        api_type: apiType
      });
      
      let url = `/api/v1/ecommerce/registry/platforms?${params}`;
      
      return createApiRequest<{ platform_id: string; name: string; icon: string }>(
        url,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: configSchema ? JSON.stringify({ config_schema: configSchema }) : undefined
        }
      );
    },
  },

  auth: {
    login: async (data: LoginRequest) => {
      return createApiRequest<{ user: User; token: string }>('/api/v1/auth/login', {
        method: 'POST',
        body: JSON.stringify(data),
      });
    },

    register: async (data: RegisterRequest) => {
      return createApiRequest<{ user: User; token: string }>('/api/v1/auth/register', {
        method: 'POST',
        body: JSON.stringify(data),
      });
    },

    logout: async () => {
      return createApiRequest<void>('/api/v1/auth/logout', { method: 'POST' });
    },

    getCurrentUser: async () => {
      return createApiRequest<User>('/api/v1/auth/me');
    },
  },

  chat: {
    send: async (message: string, enterpriseId?: string) => {
      return createApiRequest<{ content: string; sources?: unknown[] }>('/api/v1/chat/sessions', {
        method: 'POST',
        body: JSON.stringify({ message, enterpriseId }),
      });
    },

    sendSSE: async (
      message: string,
      enterpriseId: string,
      onChunk: (chunk: string) => void,
      onEnd: () => void,
      onError: (error: string) => void
    ) => {
      const baseUrl = getBaseUrl();
      const url = `${baseUrl}/api/v1/chat/stream`;

      try {
        const response = await fetch(url, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(authToken ? { 'Authorization': `Bearer ${authToken}` } : {}),
          },
          body: JSON.stringify({ message, enterpriseId }),
        });

        if (!response.ok) {
          onError(`Request failed: ${response.status}`);
          return;
        }

        const reader = response.body?.getReader();
        if (!reader) {
          onError('No response body');
          return;
        }

        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.slice(6);
              if (data === '[DONE]') {
                onEnd();
                return;
              }
              try {
                const parsed = JSON.parse(data);
                if (parsed.content) {
                  onChunk(parsed.content);
                }
              } catch {
                onChunk(data);
              }
            }
          }
        }

        onEnd();
      } catch (error) {
        onError(error instanceof Error ? error.message : 'Stream error');
      }
    },

    getSessions: async (enterpriseId?: string, userId?: string) => {
      const params = new URLSearchParams();
      if (enterpriseId) params.append('enterprise_id', enterpriseId);
      if (userId) params.append('user_id', userId);
      return createApiRequest<{ sessions: ChatSession[] }>(
        `/api/v1/chat/sessions${params.toString() ? `?${params.toString()}` : ''}`
      );
    },

    deleteSession: async (sessionId: string, userId?: string) => {
      const params = userId ? `?user_id=${userId}` : '';
      return createApiRequest<void>(`/api/v1/chat/sessions/${sessionId}${params}`, {
        method: 'DELETE',
      });
    },
  },

  documents: {
    list: async () => {
      return createApiRequest<{ documents: Document[] }>('/api/v1/documents');
    },

    getDocuments: async (kbId: string, enterpriseId: string) => {
      return createApiRequest<{ documents: Document[] }>(`/api/v1/documents?kb_id=${kbId}&enterprise_id=${enterpriseId}`);
    },

    getKnowledgeBases: async (enterpriseId: string) => {
      return createApiRequest<{ knowledge_bases: KnowledgeBase[] }>(`/api/v1/knowledge-bases?enterprise_id=${enterpriseId}`);
    },

    createKnowledgeBase: async (name: string, enterpriseId: string) => {
      return createApiRequest<KnowledgeBase>('/api/v1/knowledge-bases', {
        method: 'POST',
        body: JSON.stringify({ name, enterprise_id: enterpriseId }),
      });
    },

    upload: async (file: File) => {
      const formData = new FormData();
      formData.append('file', file);

      const baseUrl = getBaseUrl();
      const url = `${baseUrl}/api/v1/documents/upload`;

      const headers: Record<string, string> = {};
      if (authToken) {
        headers['Authorization'] = `Bearer ${authToken}`;
      }

      const response = await fetch(url, {
        method: 'POST',
        headers,
        body: formData,
      });

      const data = await response.json() as { document_id: string; filename: string; status: string } | { message?: string };
      if (!response.ok) {
        return { error: (data as { message?: string }).message || 'Upload failed' } as ApiResponse<{ document_id: string; filename: string; status: string }>;
      }

      return { data: data as { document_id: string; filename: string; status: string } };
    },

    uploadDocument: async (kbId: string, enterpriseId: string, file: File) => {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('kb_id', kbId);
      formData.append('enterprise_id', enterpriseId);

      const baseUrl = getBaseUrl();
      const url = `${baseUrl}/api/v1/documents/upload`;

      const headers: Record<string, string> = {};
      if (authToken) {
        headers['Authorization'] = `Bearer ${authToken}`;
      }

      const response = await fetch(url, {
        method: 'POST',
        headers,
        body: formData,
      });

      const data = await response.json();
      if (!response.ok) {
        return { error: data.message || 'Upload failed' };
      }

      return { data };
    },

    delete: async (id: string) => {
      return createApiRequest<void>(`/api/v1/documents/${id}`, { method: 'DELETE' });
    },

    deleteDocument: async (docId: string, enterpriseId: string) => {
      return createApiRequest<void>(`/api/v1/documents/${docId}?enterprise_id=${enterpriseId}`, { method: 'DELETE' });
    },
  },

  sensitive: {
    getSettings: async () => {
      return createApiRequest<SensitiveSettings>('/api/v1/sensitive-settings');
    },

    getSensitiveSettings: async (_enterpriseId: string) => {
      return createApiRequest<SensitiveSettings>('/api/v1/sensitive-settings');
    },

    updateSettings: async (settings: SensitiveSettings) => {
      return createApiRequest<SensitiveSettings>('/api/v1/sensitive-settings', {
        method: 'PUT',
        body: JSON.stringify(settings),
      });
    },

    updateSensitiveSettings: async (_enterpriseId: string, settings: SensitiveSettings) => {
      return createApiRequest<SensitiveSettings>('/api/v1/sensitive-settings', {
        method: 'PUT',
        body: JSON.stringify(settings),
      });
    },

    createSemanticRule: async (rule: Omit<SemanticRule, 'id'>) => {
      return createApiRequest<SemanticRule>('/api/v1/semantic-rules', {
        method: 'POST',
        body: JSON.stringify(rule),
      });
    },

    deleteSemanticRule: async (id: string) => {
      return createApiRequest<void>(`/api/v1/semantic-rules/${id}`, { method: 'DELETE' });
    },
  },

  enterprises: {
    create: async (name: string) => {
      return createApiRequest<{ id: string }>('/api/v1/enterprises', {
        method: 'POST',
        body: JSON.stringify({ name }),
      });
    },

    get: async (id: string) => {
      return createApiRequest<Enterprise>(`/api/v1/enterprises/${id}`);
    },

    list: async () => {
      return createApiRequest<{ enterprises: Enterprise[] }>('/api/v1/enterprises');
    },

    update: async (id: string, data: Partial<Enterprise>) => {
      return createApiRequest<Enterprise>(`/api/v1/enterprises/${id}`, {
        method: 'PUT',
        body: JSON.stringify(data),
      });
    },

    delete: async (id: string) => {
      return createApiRequest<void>(`/api/v1/enterprises/${id}`, {
        method: 'DELETE',
      });
    },

    getStats: async (id: string) => {
      return createApiRequest<{ userCount: number; documentCount: number; sessionCount: number }>(
        `/api/v1/enterprises/${id}/stats`
      );
    },
  },

  admin: {
    users: {
      list: async (enterpriseId?: string) => {
        const params = enterpriseId ? `?enterprise_id=${enterpriseId}` : '';
        return createApiRequest<{ users: User[] }>(`/api/v1/admin/users${params}`);
      },

      get: async (userId: string) => {
        return createApiRequest<User>(`/api/v1/admin/users/${userId}`);
      },

      create: async (data: Omit<User, 'id'>) => {
        return createApiRequest<User>('/api/v1/admin/users', {
          method: 'POST',
          body: JSON.stringify(data),
        });
      },

      update: async (userId: string, data: Partial<User>) => {
        return createApiRequest<User>(`/api/v1/admin/users/${userId}`, {
          method: 'PUT',
          body: JSON.stringify(data),
        });
      },

      delete: async (userId: string) => {
        return createApiRequest<void>(`/api/v1/admin/users/${userId}`, {
          method: 'DELETE',
        });
      },
    },

    alerts: {
      list: async (status?: string, level?: string, enterpriseId?: string) => {
        const params = new URLSearchParams();
        if (status) params.append('status', status);
        if (level) params.append('level', level);
        if (enterpriseId) params.append('enterprise_id', enterpriseId);
        return createApiRequest<{ alerts: Alert[] }>(
          `/api/v1/admin/alerts${params.toString() ? `?${params.toString()}` : ''}`
        );
      },

      get: async (alertId: string) => {
        return createApiRequest<Alert>(`/api/v1/admin/alerts/${alertId}`);
      },

      acknowledge: async (alertId: string) => {
        return createApiRequest<void>(`/api/v1/admin/alerts/${alertId}/acknowledge`, {
          method: 'POST',
        });
      },

      resolve: async (alertId: string) => {
        return createApiRequest<void>(`/api/v1/admin/alerts/${alertId}/resolve`, {
          method: 'POST',
        });
      },

      delete: async (alertId: string) => {
        return createApiRequest<void>(`/api/v1/admin/alerts/${alertId}`, {
          method: 'DELETE',
        });
      },
    },

    analytics: {
      getStats: async (enterpriseId?: string) => {
        const params = enterpriseId ? `?enterprise_id=${enterpriseId}` : '';
        return createApiRequest<AnalyticsStats>(`/api/v1/admin/analytics${params}`);
      },

      getEnterpriseStats: async (enterpriseId: string) => {
        return createApiRequest<AnalyticsStats>(`/api/v1/admin/analytics?enterprise_id=${enterpriseId}`);
      },
    },

    services: {
      list: async () => {
        return createApiRequest<{ services: ServiceStatus[] }>('/api/v1/admin/services');
      },
    },
  },
};

export { type SemanticRule, type SensitiveSettings };
