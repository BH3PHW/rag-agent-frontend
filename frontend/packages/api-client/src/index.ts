import type { 
  User, 
  Enterprise, 
  KnowledgeBase, 
  Document, 
  ChatSession,
  Alert,
  AnalyticsStats,
  ServiceHealth,
  ApiResponse,
  LoginResponse,
  LoginRequest,
  RegisterRequest
} from './types';

export const API_CONFIG = {
  DEFAULT_BASE_URL: 'http://localhost:8000',
  TOKEN_KEY: 'rag_api_token',
  STORAGE_KEY: 'rag-api-settings',
} as const;

let baseUrl: string = API_CONFIG.DEFAULT_BASE_URL;
let authToken: string | null = null;

export const setBaseUrl = (url: string): void => {
  baseUrl = url;
};

export const getBaseUrl = (): string => {
  if (typeof window !== 'undefined') {
    try {
      const stored = localStorage.getItem(API_CONFIG.STORAGE_KEY);
      if (stored) {
        const settings = JSON.parse(stored);
        const defaultConfig = settings.configs?.find(
          (c: { id: string }) => c.id === settings.defaultConfig
        );
        return defaultConfig?.baseUrl || baseUrl;
      }
    } catch {}
  }
  return baseUrl;
};

export const setToken = (token: string | null): void => {
  authToken = token;
  if (token) {
    localStorage.setItem(API_CONFIG.TOKEN_KEY, token);
  } else {
    localStorage.removeItem(API_CONFIG.TOKEN_KEY);
  }
};

export const getToken = (): string | null => {
  if (authToken) return authToken;
  if (typeof window !== 'undefined') {
    return localStorage.getItem(API_CONFIG.TOKEN_KEY);
  }
  return null;
};

const getHeaders = (): HeadersInit => {
  const token = getToken();
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
};

const snakeToCamel = (str: string): string => {
  return str.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase());
};

const transformObjectKeys = <T>(obj: any): T => {
  if (typeof obj !== 'object' || obj === null) {
    return obj;
  }
  if (Array.isArray(obj)) {
    return obj.map(item => transformObjectKeys(item)) as unknown as T;
  }
  const result: Record<string, unknown> = {};
  for (const key of Object.keys(obj)) {
    const camelKey = snakeToCamel(key);
    result[camelKey] = transformObjectKeys(obj[key]);
  }
  return result as T;
};

const createRequest = async <T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> => {
  const url = `${getBaseUrl()}${endpoint}`;

  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        ...getHeaders(),
        ...(options.headers as Record<string, string>),
      },
    });

    const data = await response.json();

    if (!response.ok) {
      return { 
        error: data.message || `Request failed: ${response.status}`,
        data: undefined 
      };
    }

    const transformedData = transformObjectKeys<T>(data);
    return { data: transformedData };
  } catch (error) {
    return { 
      error: error instanceof Error ? error.message : 'Network error',
      data: undefined
    };
  }
};

export interface AuthApi {
  login: (data: LoginRequest) => Promise<ApiResponse<LoginResponse>>;
  register: (data: RegisterRequest) => Promise<ApiResponse<LoginResponse>>;
  logout: () => Promise<ApiResponse<void>>;
  getCurrentUser: () => Promise<ApiResponse<User>>;
}

export interface ChatApi {
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
}

export interface DocumentApi {
  list: () => Promise<ApiResponse<{ documents: Document[] }>>;
  getDocuments: (kbId: string, enterpriseId: string) => Promise<ApiResponse<{ documents: Document[] }>>;
  getKnowledgeBases: (enterpriseId: string) => Promise<ApiResponse<{ knowledge_bases: KnowledgeBase[] }>>;
  createKnowledgeBase: (name: string, enterpriseId: string) => Promise<ApiResponse<KnowledgeBase>>;
  upload: (file: File) => Promise<ApiResponse<unknown>>;
  uploadDocument: (kbId: string, enterpriseId: string, file: File) => Promise<ApiResponse<Document>>;
  delete: (id: string) => Promise<ApiResponse<void>>;
  deleteDocument: (docId: string, enterpriseId: string) => Promise<ApiResponse<void>>;
}

export interface EnterpriseApi {
  create: (name: string) => Promise<ApiResponse<{ id: string }>>;
  get: (id: string) => Promise<ApiResponse<Enterprise>>;
  list: () => Promise<ApiResponse<{ enterprises: Enterprise[] }>>;
  update: (id: string, data: Partial<Enterprise>) => Promise<ApiResponse<Enterprise>>;
  delete: (id: string) => Promise<ApiResponse<void>>;
  getStats: (id: string) => Promise<ApiResponse<{ userCount: number; documentCount: number; sessionCount: number }>>;
}

export interface AdminApi {
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
    list: () => Promise<ApiResponse<{ services: ServiceHealth[] }>>;
  };
}

export interface ApiClient {
  setBaseUrl: (url: string) => void;
  getBaseUrl: () => string;
  setToken: (token: string | null) => void;
  getToken: () => string | null;
  auth: AuthApi;
  chat: ChatApi;
  documents: DocumentApi;
  enterprises: EnterpriseApi;
  admin: AdminApi;
}

export const createApiClient = (): ApiClient => {
  const auth: AuthApi = {
    login: async (data: LoginRequest) => {
      return createRequest<LoginResponse>('/api/v1/auth/login', {
        method: 'POST',
        body: JSON.stringify(data),
      });
    },

    register: async (data: RegisterRequest) => {
      return createRequest<LoginResponse>('/api/v1/auth/register', {
        method: 'POST',
        body: JSON.stringify(data),
      });
    },

    logout: async () => {
      return createRequest<void>('/api/v1/auth/logout', { method: 'POST' });
    },

    getCurrentUser: async () => {
      return createRequest<User>('/api/v1/auth/me');
    },
  };

  const chat: ChatApi = {
    send: async (message: string, enterpriseId?: string) => {
      return createRequest<{ content: string; sources?: unknown[] }>('/api/v1/chat/sessions', {
        method: 'POST',
        body: JSON.stringify({ message, enterpriseId }),
      });
    },

    sendSSE: async (message, enterpriseId, onChunk, onEnd, onError) => {
      const url = `${getBaseUrl()}/api/v1/chat/stream`;

      try {
        const response = await fetch(url, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(getToken() ? { Authorization: `Bearer ${getToken()}` } : {}),
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
      return createRequest<{ sessions: ChatSession[] }>(
        `/api/v1/chat/sessions${params.toString() ? `?${params.toString()}` : ''}`
      );
    },

    deleteSession: async (sessionId: string, userId?: string) => {
      const params = userId ? `?user_id=${userId}` : '';
      return createRequest<void>(`/api/v1/chat/sessions/${sessionId}${params}`, {
        method: 'DELETE',
      });
    },
  };

  const documents: DocumentApi = {
    list: async () => {
      return createRequest<{ documents: Document[] }>('/api/v1/documents');
    },

    getDocuments: async (kbId: string, enterpriseId: string) => {
      return createRequest<{ documents: Document[] }>(
        `/api/v1/documents?kb_id=${kbId}&enterprise_id=${enterpriseId}`
      );
    },

    getKnowledgeBases: async (enterpriseId: string) => {
      return createRequest<{ knowledge_bases: KnowledgeBase[] }>(
        `/api/v1/knowledge-bases?enterprise_id=${enterpriseId}`
      );
    },

    createKnowledgeBase: async (name: string, enterpriseId: string) => {
      return createRequest<KnowledgeBase>('/api/v1/knowledge-bases', {
        method: 'POST',
        body: JSON.stringify({ name, enterprise_id: enterpriseId }),
      });
    },

    upload: async (file: File) => {
      const formData = new FormData();
      formData.append('file', file);

      const url = `${getBaseUrl()}/api/v1/documents/upload`;
      const token = getToken();

      const response = await fetch(url, {
        method: 'POST',
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: formData,
      });

      const data = await response.json();
      if (!response.ok) {
        return { error: data.message || 'Upload failed' };
      }
      return { data };
    },

    uploadDocument: async (kbId: string, enterpriseId: string, file: File) => {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('kb_id', kbId);
      formData.append('enterprise_id', enterpriseId);

      const url = `${getBaseUrl()}/api/v1/documents/upload`;
      const token = getToken();

      const response = await fetch(url, {
        method: 'POST',
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: formData,
      });

      const data = await response.json();
      if (!response.ok) {
        return { error: data.message || 'Upload failed' };
      }
      return { data };
    },

    delete: async (id: string) => {
      return createRequest<void>(`/api/v1/documents/${id}`, { method: 'DELETE' });
    },

    deleteDocument: async (docId: string, enterpriseId: string) => {
      return createRequest<void>(
        `/api/v1/documents/${docId}?enterprise_id=${enterpriseId}`,
        { method: 'DELETE' }
      );
    },
  };

  const enterprises: EnterpriseApi = {
    create: async (name: string) => {
      return createRequest<{ id: string }>('/api/v1/enterprises', {
        method: 'POST',
        body: JSON.stringify({ name }),
      });
    },

    get: async (id: string) => {
      return createRequest<Enterprise>(`/api/v1/enterprises/${id}`);
    },

    list: async () => {
      return createRequest<{ enterprises: Enterprise[] }>('/api/v1/enterprises');
    },

    update: async (id: string, data: Partial<Enterprise>) => {
      return createRequest<Enterprise>(`/api/v1/enterprises/${id}`, {
        method: 'PUT',
        body: JSON.stringify(data),
      });
    },

    delete: async (id: string) => {
      return createRequest<void>(`/api/v1/enterprises/${id}`, { method: 'DELETE' });
    },

    getStats: async (id: string) => {
      return createRequest<{ userCount: number; documentCount: number; sessionCount: number }>(
        `/api/v1/enterprises/${id}/stats`
      );
    },
  };

  const admin: AdminApi = {
    users: {
      list: async (enterpriseId?: string) => {
        const params = enterpriseId ? `?enterprise_id=${enterpriseId}` : '';
        return createRequest<{ users: User[] }>(`/api/v1/admin/users${params}`);
      },

      get: async (userId: string) => {
        return createRequest<User>(`/api/v1/admin/users/${userId}`);
      },

      create: async (data: Omit<User, 'id'>) => {
        return createRequest<User>('/api/v1/admin/users', {
          method: 'POST',
          body: JSON.stringify(data),
        });
      },

      update: async (userId: string, data: Partial<User>) => {
        return createRequest<User>(`/api/v1/admin/users/${userId}`, {
          method: 'PUT',
          body: JSON.stringify(data),
        });
      },

      delete: async (userId: string) => {
        return createRequest<void>(`/api/v1/admin/users/${userId}`, { method: 'DELETE' });
      },
    },

    alerts: {
      list: async (status?: string, level?: string, enterpriseId?: string) => {
        const params = new URLSearchParams();
        if (status) params.append('status', status);
        if (level) params.append('level', level);
        if (enterpriseId) params.append('enterprise_id', enterpriseId);
        return createRequest<{ alerts: Alert[] }>(
          `/api/v1/admin/alerts${params.toString() ? `?${params.toString()}` : ''}`
        );
      },

      get: async (alertId: string) => {
        return createRequest<Alert>(`/api/v1/admin/alerts/${alertId}`);
      },

      acknowledge: async (alertId: string) => {
        return createRequest<void>(`/api/v1/admin/alerts/${alertId}/acknowledge`, {
          method: 'POST',
        });
      },

      resolve: async (alertId: string) => {
        return createRequest<void>(`/api/v1/admin/alerts/${alertId}/resolve`, {
          method: 'POST',
        });
      },

      delete: async (alertId: string) => {
        return createRequest<void>(`/api/v1/admin/alerts/${alertId}`, { method: 'DELETE' });
      },
    },

    analytics: {
      getStats: async (enterpriseId?: string) => {
        const params = enterpriseId ? `?enterprise_id=${enterpriseId}` : '';
        return createRequest<AnalyticsStats>(`/api/v1/admin/analytics${params}`);
      },

      getEnterpriseStats: async (enterpriseId: string) => {
        return createRequest<AnalyticsStats>(
          `/api/v1/admin/analytics?enterprise_id=${enterpriseId}`
        );
      },
    },

    services: {
      list: async () => {
        return createRequest<{ services: ServiceHealth[] }>('/api/v1/admin/services');
      },
    },
  };

  return {
    setBaseUrl,
    getBaseUrl,
    setToken,
    getToken,
    auth,
    chat,
    documents,
    enterprises,
    admin,
  };
};

export const api = createApiClient();