export interface ApiConfig {
  id: string;
  name: string;
  baseUrl: string;
  timeout: number;
  retryAttempts: number;
  headers: Record<string, string>;
  enabled: boolean;
}

export interface GlobalApiSettings {
  defaultConfig: string;
  configs: ApiConfig[];
  autoRetry: boolean;
  logRequests: boolean;
}

export const defaultApiSettings: GlobalApiSettings = {
  defaultConfig: 'default',
  configs: [
    {
      id: 'default',
      name: '默认配置',
      baseUrl: 'http://localhost:8000',
      timeout: 30000,
      retryAttempts: 3,
      headers: {
        'Content-Type': 'application/json',
      },
      enabled: true,
    },
  ],
  autoRetry: true,
  logRequests: false,
};

const STORAGE_KEY = 'rag-api-settings';

export function loadApiSettings(): GlobalApiSettings {
  if (typeof window === 'undefined') return defaultApiSettings;
  
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      return { ...defaultApiSettings, ...JSON.parse(stored) };
    }
  } catch (error) {
    console.error('[ApiConfig] Failed to load API settings:', error);
  }
  return defaultApiSettings;
}

export function saveApiSettings(settings: GlobalApiSettings): void {
  if (typeof window === 'undefined') return;
  
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
  } catch (error) {
    console.error('[ApiConfig] Failed to save API settings:', error);
  }
}

export function getActiveApiConfig(settings?: GlobalApiSettings): ApiConfig {
  const currentSettings = settings || loadApiSettings();
  const activeConfig = currentSettings.configs.find(
    c => c.id === currentSettings.defaultConfig
  );
  return activeConfig || currentSettings.configs[0] || defaultApiSettings.configs[0];
}

export function getApiBaseUrl(): string {
  const config = getActiveApiConfig();
  return config.baseUrl;
}
