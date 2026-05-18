import { getApiBaseUrl, getActiveApiConfig, type ApiConfig } from './apiConfig';

export { type ApiConfig } from './apiConfig';

interface RequestOptions extends RequestInit {
  token?: string;
  skipApiPrefix?: boolean;
}

export async function apiRequest<T>(
  endpoint: string,
  options: RequestOptions = {}
): Promise<T> {
  const { token, skipApiPrefix, ...fetchOptions } = options;
  
  const config = getActiveApiConfig();
  
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...config.headers,
    ...(fetchOptions.headers as Record<string, string>),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const baseUrl = getApiBaseUrl();
  const apiPrefix = skipApiPrefix ? '' : '/api/v1';
  const url = `${baseUrl}${apiPrefix}${endpoint}`;

  if (config.enabled && config.id !== 'default') {
    console.log(`[API] ${options.method || 'GET'} ${url}`);
  }

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), config.timeout);

  try {
    const response = await fetch(url, {
      ...fetchOptions,
      headers,
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.message || `Request failed: ${response.status}`);
    }

    return response.json();
  } catch (error) {
    clearTimeout(timeoutId);
    
    if (error instanceof Error && error.name === 'AbortError') {
      throw new Error('请求超时');
    }
    
    throw error;
  }
}

export async function testApiConnection(config: ApiConfig): Promise<{
  success: boolean;
  message: string;
  latency?: number;
}> {
  const startTime = Date.now();
  
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), config.timeout);
    
    const response = await fetch(`${config.baseUrl}/api/v1/health`, {
      method: 'GET',
      headers: config.headers,
      signal: controller.signal,
    });
    
    clearTimeout(timeoutId);
    
    if (response.ok) {
      return {
        success: true,
        message: '连接成功',
        latency: Date.now() - startTime,
      };
    } else {
      return {
        success: false,
        message: `连接失败: ${response.status} ${response.statusText}`,
        latency: Date.now() - startTime,
      };
    }
  } catch (error) {
    if (error instanceof Error) {
      if (error.name === 'AbortError') {
        return {
          success: false,
          message: '连接超时',
          latency: Date.now() - startTime,
        };
      }
      return {
        success: false,
        message: `连接错误: ${error.message}`,
        latency: Date.now() - startTime,
      };
    }
    return {
      success: false,
      message: '未知错误',
      latency: Date.now() - startTime,
    };
  }
}
