import type { Enterprise, Alert, ServiceHealth, AnalyticsStats, SystemUser } from '../auth/types';
import { useAuthStore } from '../auth/store';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

interface ApiResponse<T> {
  data?: T;
  error?: string;
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private getHeaders(): HeadersInit {
    const token = localStorage.getItem('sap_token');
    return {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    };
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        ...options,
        headers: this.getHeaders(),
      });

      const data = await response.json();

      if (!response.ok) {
        return { error: data.message || `Request failed: ${response.status}` };
      }

      return { data };
    } catch (error) {
      return { error: error instanceof Error ? error.message : 'Network error' };
    }
  }

  async get<T>(endpoint: string): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { method: 'GET' });
  }

  async post<T>(endpoint: string, body?: unknown): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: body ? JSON.stringify(body) : undefined,
    });
  }

  async put<T>(endpoint: string, body?: unknown): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: body ? JSON.stringify(body) : undefined,
    });
  }

  async delete<T>(endpoint: string): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { method: 'DELETE' });
  }

  async getEnterprises(): Promise<ApiResponse<{ enterprises: Enterprise[] }>> {
    return this.get<{ enterprises: Enterprise[] }>('/api/v1/admin/enterprises');
  }

  async getEnterprise(id: string): Promise<ApiResponse<Enterprise>> {
    return this.get<Enterprise>(`/api/v1/admin/enterprises/${id}`);
  }

  async createEnterprise(data: { name: string }): Promise<ApiResponse<Enterprise>> {
    return this.post<Enterprise>('/api/v1/admin/enterprises', data);
  }

  async updateEnterprise(id: string, data: Partial<Enterprise>): Promise<ApiResponse<Enterprise>> {
    return this.put<Enterprise>(`/api/v1/admin/enterprises/${id}`, data);
  }

  async deleteEnterprise(id: string): Promise<ApiResponse<void>> {
    return this.delete<void>(`/api/v1/admin/enterprises/${id}`);
  }

  async getUsers(): Promise<ApiResponse<{ users: SystemUser[] }>> {
    return this.get<{ users: SystemUser[] }>('/api/v1/admin/users');
  }

  async getUser(id: string): Promise<ApiResponse<SystemUser>> {
    return this.get<SystemUser>(`/api/v1/admin/users/${id}`);
  }

  async createUser(data: Omit<SystemUser, 'id'>): Promise<ApiResponse<SystemUser>> {
    return this.post<SystemUser>('/api/v1/admin/users', data);
  }

  async updateUser(id: string, data: Partial<SystemUser>): Promise<ApiResponse<SystemUser>> {
    return this.put<SystemUser>(`/api/v1/admin/users/${id}`, data);
  }

  async deleteUser(id: string): Promise<ApiResponse<void>> {
    return this.delete<void>(`/api/v1/admin/users/${id}`);
  }

  async getServices(): Promise<ApiResponse<{ services: ServiceHealth[] }>> {
    return this.get<{ services: ServiceHealth[] }>('/api/v1/admin/services');
  }

  async getAlerts(status?: string): Promise<ApiResponse<{ alerts: Alert[] }>> {
    const params = status ? `?status=${status}` : '';
    return this.get<{ alerts: Alert[] }>(`/api/v1/admin/alerts${params}`);
  }

  async acknowledgeAlert(id: string): Promise<ApiResponse<void>> {
    return this.post<void>(`/api/v1/admin/alerts/${id}/acknowledge`);
  }

  async resolveAlert(id: string): Promise<ApiResponse<void>> {
    return this.post<void>(`/api/v1/admin/alerts/${id}/resolve`);
  }

  async deleteAlert(id: string): Promise<ApiResponse<void>> {
    return this.delete<void>(`/api/v1/admin/alerts/${id}`);
  }

  async getAnalytics(): Promise<ApiResponse<AnalyticsStats>> {
    return this.get<AnalyticsStats>('/api/v1/admin/analytics');
  }

  async getConfig(): Promise<ApiResponse<Record<string, unknown>>> {
    return this.get<Record<string, unknown>>('/api/v1/admin/config');
  }

  async updateConfig(config: Record<string, unknown>): Promise<ApiResponse<Record<string, unknown>>> {
    return this.put<Record<string, unknown>>('/api/v1/admin/config', config);
  }
}

export const api = new ApiClient(API_BASE_URL);