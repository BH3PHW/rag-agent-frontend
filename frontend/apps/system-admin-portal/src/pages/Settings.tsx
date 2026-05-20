import React, { useState, useEffect } from 'react';
import { Settings as SettingsIcon, Save, RefreshCw } from 'lucide-react';
import { api } from '../api/client';
import { Loader2 } from 'lucide-react';

interface SystemConfig {
  apiGatewayUrl: string;
  maxUploadSize: number;
  sessionTimeout: number;
  enableDebugMode: boolean;
  maintenanceMode: boolean;
}

export default function SettingsPage() {
  const [config, setConfig] = useState<SystemConfig>({
    apiGatewayUrl: 'http://localhost:8080',
    maxUploadSize: 50,
    sessionTimeout: 3600,
    enableDebugMode: false,
    maintenanceMode: false,
  });
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await api.getConfig();
      if (result.error) throw new Error(result.error);
      if (result.data) {
        setConfig({ ...config, ...(result.data as SystemConfig) });
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load config');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = async () => {
    setIsSaving(true);
    setError(null);
    setSuccess(false);
    try {
      const result = await api.updateConfig(config);
      if (result.error) throw new Error(result.error);
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save config');
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="w-8 h-8 animate-spin text-emerald-600" />
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">系统设置</h3>
          <p className="text-gray-500">配置系统参数和选项</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={loadConfig}
            className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            <RefreshCw className="w-4 h-4" />
            重置
          </button>
          <button
            onClick={handleSave}
            disabled={isSaving}
            className="flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 disabled:opacity-50"
          >
            {isSaving ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Save className="w-4 h-4" />
            )}
            保存设置
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
          {error}
        </div>
      )}

      {success && (
        <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg mb-6">
          设置保存成功！
        </div>
      )}

      <div className="space-y-6">
        <div className="card p-6">
          <h4 className="font-semibold text-gray-900 mb-4">API 配置</h4>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                API Gateway 地址
              </label>
              <input
                type="text"
                value={config.apiGatewayUrl}
                onChange={(e) => setConfig({ ...config, apiGatewayUrl: e.target.value })}
                className="input"
                placeholder="http://localhost:8080"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                最大上传大小 (MB)
              </label>
              <input
                type="number"
                value={config.maxUploadSize}
                onChange={(e) => setConfig({ ...config, maxUploadSize: parseInt(e.target.value) })}
                className="input"
                min="1"
                max="500"
              />
            </div>
          </div>
        </div>

        <div className="card p-6">
          <h4 className="font-semibold text-gray-900 mb-4">安全设置</h4>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                会话超时时间 (秒)
              </label>
              <input
                type="number"
                value={config.sessionTimeout}
                onChange={(e) => setConfig({ ...config, sessionTimeout: parseInt(e.target.value) })}
                className="input"
                min="300"
                max="86400"
              />
            </div>
          </div>
        </div>

        <div className="card p-6">
          <h4 className="font-semibold text-gray-900 mb-4">系统模式</h4>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-gray-900">调试模式</p>
                <p className="text-sm text-gray-500">启用详细的日志输出</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={config.enableDebugMode}
                  onChange={(e) => setConfig({ ...config, enableDebugMode: e.target.checked })}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-emerald-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-emerald-600"></div>
              </label>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-gray-900">维护模式</p>
                <p className="text-sm text-gray-500">阻止普通用户访问系统</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={config.maintenanceMode}
                  onChange={(e) => setConfig({ ...config, maintenanceMode: e.target.checked })}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-emerald-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-emerald-600"></div>
              </label>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}