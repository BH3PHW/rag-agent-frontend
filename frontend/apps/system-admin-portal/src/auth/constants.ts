export enum SystemRole {
  SYSTEM_ADMIN = 'system_admin',
}

export const SYSTEM_ADMIN_ONLY_ROUTES = [
  '/dashboard',
  '/tenants',
  '/users',
  '/services',
  '/analytics',
  '/alerts',
  '/settings',
];

export const API_ENDPOINTS = {
  AUTH: {
    LOGIN: '/api/v1/auth/login',
    LOGOUT: '/api/v1/auth/logout',
    REFRESH: '/api/v1/auth/refresh',
    VERIFY: '/api/v1/auth/verify',
  },
  ADMIN: {
    USERS: '/api/v1/admin/users',
    ENTERPRISES: '/api/v1/admin/enterprises',
    SERVICES: '/api/v1/admin/services',
    ANALYTICS: '/api/v1/admin/analytics',
    ALERTS: '/api/v1/admin/alerts',
    CONFIG: '/api/v1/admin/config',
  },
} as const;

export const AUTH_CONFIG = {
  TOKEN_KEY: 'sap_token',
  REFRESH_TOKEN_KEY: 'sap_refresh_token',
  TOKEN_EXPIRY_BUFFER: 5 * 60,
  API_TIMEOUT: 30000,
} as const;