export interface SystemUser {
  id: string;
  username: string;
  email: string;
  role: 'system_admin';
  createdAt: string;
  lastLoginAt?: string;
}

export interface AuthTokens {
  accessToken: string;
  refreshToken: string;
  expiresIn: number;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface LoginResponse {
  user: SystemUser;
  tokens: AuthTokens;
}

export interface ApiResponse<T> {
  data?: T;
  error?: string;
  message?: string;
}

export interface ServiceHealth {
  name: string;
  status: 'healthy' | 'degraded' | 'down';
  uptime: string;
  version: string;
}

export interface Enterprise {
  id: string;
  name: string;
  plan: string;
  userCount: number;
  documentCount: number;
  sessionCount: number;
  status: 'active' | 'suspended';
  createdAt: string;
}

export interface Alert {
  id: string;
  type: 'security' | 'system' | 'usage';
  level: 'info' | 'warning' | 'critical';
  message: string;
  status: 'active' | 'acknowledged' | 'resolved';
  createdAt: string;
}

export interface AnalyticsStats {
  totalSessions: number;
  totalMessages: number;
  totalUsers: number;
  totalDocuments: number;
  activeTenants: number;
}