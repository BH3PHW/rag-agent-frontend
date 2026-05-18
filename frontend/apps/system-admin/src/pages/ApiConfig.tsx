import { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  Button,
  Input,
  Tag
} from '@rag/ui';
import {
  Globe,
  Plus,
  Trash2,
  Edit2,
  TestTube,
  CheckCircle2,
  XCircle,
  AlertCircle,
  RefreshCw
} from 'lucide-react';
import {
  GlobalApiSettings,
  defaultApiSettings,
  loadApiSettings,
  saveApiSettings,
  testApiConnection,
  getActiveApiConfig,
  ApiConfig
} from '@rag/store';

export default function ApiConfigPage() {
  const [settings, setSettings] = useState<GlobalApiSettings>(defaultApiSettings);
  const [editingConfig, setEditingConfig] = useState<ApiConfig | null>(null);
  const [testResults, setTestResults] = useState<Record<string, { success: boolean; message: string; latency?: number }>>({});
  const [selectedConfigId, setSelectedConfigId] = useState<string>('default');

  useEffect(() => {
    const loaded = loadApiSettings();
    setSettings(loaded);
    setSelectedConfigId(loaded.defaultConfig);
  }, []);

  const handleSave = () => {
    saveApiSettings(settings);
    window.dispatchEvent(new Event('storage'));
    alert('API 配置已保存！前端将立即使用新配置。');
  };

  const handleAddConfig = () => {
    const newConfig: ApiConfig = {
      id: `config-${Date.now()}`,
      name: '新配置',
      baseUrl: 'https://',
      timeout: 30000,
      retryAttempts: 3,
      headers: { 'Content-Type': 'application/json' },
      enabled: false,
    };
    setSettings(prev => ({
      ...prev,
      configs: [...prev.configs, newConfig],
    }));
    setEditingConfig(newConfig);
  };

  const handleDeleteConfig = (id: string) => {
    if (settings.configs.length <= 1) {
      alert('至少需要保留一个配置！');
      return;
    }
    if (confirm('确定要删除这个配置吗？')) {
      setSettings(prev => ({
        ...prev,
        configs: prev.configs.filter(c => c.id !== id),
      }));
    }
  };

  const handleUpdateConfig = (updated: ApiConfig) => {
    setSettings(prev => ({
      ...prev,
      configs: prev.configs.map(c => c.id === updated.id ? updated : c),
    }));
    setEditingConfig(updated);
  };

  const handleTestConnection = async (config: ApiConfig) => {
    setTestResults(prev => ({
      ...prev,
      [config.id]: { success: false, message: '测试中...' },
    }));

    const result = await testApiConnection(config);
    setTestResults(prev => ({
      ...prev,
      [config.id]: result,
    }));
  };

  const handleSetDefault = (id: string) => {
    setSettings(prev => ({
      ...prev,
      defaultConfig: id,
    }));
    setSelectedConfigId(id);
  };

  const handleCopyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    alert('已复制到剪贴板！');
  };

  const handleExportConfig = () => {
    const config = {
      version: '1.0',
      timestamp: new Date().toISOString(),
      settings: settings,
    };
    const blob = new Blob([JSON.stringify(config, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `api-config-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleImportConfig = () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.json';
    input.onchange = (e) => {
      const file = (e.target as HTMLInputElement).files?.[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = (event) => {
          try {
            const imported = JSON.parse(event.target?.result as string);
            if (imported.settings && imported.settings.configs) {
              setSettings(imported.settings);
              alert('配置导入成功！');
            } else {
              alert('无效的配置文件格式！');
            }
          } catch {
            alert('配置文件解析失败！');
          }
        };
        reader.readAsText(file);
      }
    };
    input.click();
  };

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">API 配置管理</h2>
          <p className="text-gray-500">管理系统中所有前后端 API 调用配置</p>
        </div>
        <div className="flex gap-3">
          <Button variant="secondary" onClick={handleImportConfig}>
            导入配置
          </Button>
          <Button variant="secondary" onClick={handleExportConfig}>
            导出配置
          </Button>
          <Button onClick={handleSave}>
            保存配置
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 mb-8">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">配置数量</p>
                <p className="text-2xl font-bold text-gray-900">{settings.configs.length}</p>
              </div>
              <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center">
                <Globe className="w-6 h-6 text-blue-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">当前使用</p>
                <p className="text-lg font-bold text-green-600">
                  {settings.configs.find(c => c.id === selectedConfigId)?.name || '未选择'}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">自动重试</p>
                <p className="text-lg font-bold text-gray-900">
                  {settings.autoRetry ? '已启用' : '已禁用'}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">请求日志</p>
                <p className="text-lg font-bold text-gray-900">
                  {settings.logRequests ? '已启用' : '已禁用'}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-gray-900">基础设置</h3>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-gray-700">自动重试</label>
              <input
                type="checkbox"
                checked={settings.autoRetry}
                onChange={(e) => setSettings(prev => ({ ...prev, autoRetry: e.target.checked }))}
                className="w-5 h-5 text-blue-600 rounded focus:ring-blue-500"
              />
            </div>
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-gray-700">请求日志</label>
              <input
                type="checkbox"
                checked={settings.logRequests}
                onChange={(e) => setSettings(prev => ({ ...prev, logRequests: e.target.checked }))}
                className="w-5 h-5 text-blue-600 rounded focus:ring-blue-500"
              />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <h3 className="font-semibold text-gray-900">环境变量</h3>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="bg-gray-50 rounded-lg p-3">
              <p className="text-xs text-gray-500 mb-1">开发环境</p>
              <code className="text-sm text-blue-600">VITE_API_BASE_URL</code>
            </div>
            <div className="bg-gray-50 rounded-lg p-3">
              <p className="text-xs text-gray-500 mb-1">生产环境</p>
              <code className="text-sm text-blue-600">ENVIRONMENT=production</code>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <h3 className="font-semibold text-gray-900">快速操作</h3>
          </CardHeader>
          <CardContent className="space-y-3">
            <Button
              variant="secondary"
              className="w-full"
              leftIcon={<RefreshCw className="w-4 h-4" />}
              onClick={() => {
                setSettings(defaultApiSettings);
                alert('已恢复默认配置！');
              }}
            >
              恢复默认
            </Button>
            <Button
              variant="secondary"
              className="w-full"
              leftIcon={<Globe className="w-4 h-4" />}
              onClick={() => {
                const config = getActiveApiConfig(settings);
                if (config) {
                  handleCopyToClipboard(config.baseUrl);
                }
              }}
            >
              复制当前 URL
            </Button>
          </CardContent>
        </Card>
      </div>

      <Card className="mb-6">
        <CardHeader>
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-gray-900">API 配置列表</h3>
            <Button size="sm" leftIcon={<Plus className="w-4 h-4" />} onClick={handleAddConfig}>
              添加配置
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {settings.configs.map((config) => (
            <div
              key={config.id}
              className={`border rounded-lg p-4 transition-colors ${
                selectedConfigId === config.id ? 'border-blue-500 bg-blue-50' : 'border-gray-200'
              }`}
            >
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="flex items-center gap-2">
                    {selectedConfigId === config.id && (
                      <Tag variant="success">使用中</Tag>
                    )}
                    <h4 className="font-medium text-gray-900">{config.name}</h4>
                  </div>
                  <Tag variant={config.enabled ? 'success' : 'default'}>
                    {config.enabled ? '已启用' : '已禁用'}
                  </Tag>
                </div>
                <div className="flex items-center gap-2">
                  {testResults[config.id] && (
                    <div className="flex items-center gap-1 text-sm">
                      {testResults[config.id].success ? (
                        <CheckCircle2 className="w-4 h-4 text-green-500" />
                      ) : (
                        <XCircle className="w-4 h-4 text-red-500" />
                      )}
                      <span className={testResults[config.id].success ? 'text-green-600' : 'text-red-600'}>
                        {testResults[config.id].message}
                      </span>
                      {testResults[config.id].latency && (
                        <span className="text-gray-400">({testResults[config.id].latency}ms)</span>
                      )}
                    </div>
                  )}
                  <Button
                    variant="secondary"
                    size="sm"
                    leftIcon={<TestTube className="w-4 h-4" />}
                    onClick={() => handleTestConnection(config)}
                  >
                    测试
                  </Button>
                  {selectedConfigId !== config.id && (
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => handleSetDefault(config.id)}
                    >
                      设为默认
                    </Button>
                  )}
                  <Button
                    variant="secondary"
                    size="sm"
                    leftIcon={<Edit2 className="w-4 h-4" />}
                    onClick={() => {
                      setEditingConfig(editingConfig?.id === config.id ? null : config);
                    }}
                  >
                    {editingConfig?.id === config.id ? '收起' : '编辑'}
                  </Button>
                  <Button
                    variant="danger"
                    size="sm"
                    leftIcon={<Trash2 className="w-4 h-4" />}
                    onClick={() => handleDeleteConfig(config.id)}
                  >
                    删除
                  </Button>
                </div>
              </div>

              {editingConfig?.id === config.id && (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mt-4 pt-4 border-t border-gray-200">
                  <Input
                    label="配置名称"
                    value={editingConfig.name}
                    onChange={(e) => handleUpdateConfig({ ...editingConfig, name: e.target.value })}
                    placeholder="例如：开发环境"
                  />
                  <Input
                    label="超时时间 (ms)"
                    type="number"
                    value={editingConfig.timeout}
                    onChange={(e) => handleUpdateConfig({ ...editingConfig, timeout: parseInt(e.target.value) || 30000 })}
                  />
                  <div className="lg:col-span-2">
                    <Input
                      label="API Base URL"
                      value={editingConfig.baseUrl}
                      onChange={(e) => handleUpdateConfig({ ...editingConfig, baseUrl: e.target.value })}
                      placeholder="https://api.example.com"
                    />
                  </div>
                  <Input
                    label="重试次数"
                    type="number"
                    value={editingConfig.retryAttempts}
                    onChange={(e) => handleUpdateConfig({ ...editingConfig, retryAttempts: parseInt(e.target.value) || 3 })}
                  />
                  <div className="lg:col-span-2">
                    <div className="flex items-center justify-between mb-2">
                      <label className="text-sm font-medium text-gray-700">启用配置</label>
                      <input
                        type="checkbox"
                        checked={editingConfig.enabled}
                        onChange={(e) => handleUpdateConfig({ ...editingConfig, enabled: e.target.checked })}
                        className="w-5 h-5 text-blue-600 rounded focus:ring-blue-500"
                      />
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <h3 className="font-semibold text-gray-900">使用说明</h3>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex gap-3">
            <AlertCircle className="w-5 h-5 text-blue-500 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-gray-600">
              <p className="font-medium text-gray-900 mb-1">配置切换</p>
              <p>点击"设为默认"按钮，可以随时切换前端使用的 API 配置。配置保存后立即生效，无需刷新页面。</p>
            </div>
          </div>
          <div className="flex gap-3">
            <AlertCircle className="w-5 h-5 text-blue-500 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-gray-600">
              <p className="font-medium text-gray-900 mb-1">连接测试</p>
              <p>使用"测试"按钮可以验证 API 连接是否正常。测试结果会显示响应延迟。</p>
            </div>
          </div>
          <div className="flex gap-3">
            <AlertCircle className="w-5 h-5 text-blue-500 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-gray-600">
              <p className="font-medium text-gray-900 mb-1">导入导出</p>
              <p>可以导出当前配置为 JSON 文件，便于在不同环境间迁移配置。</p>
            </div>
          </div>
          <div className="flex gap-3">
            <AlertCircle className="w-5 h-5 text-blue-500 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-gray-600">
              <p className="font-medium text-gray-900 mb-1">本地存储</p>
              <p>所有配置保存在浏览器本地存储中。如需清除，请手动清除浏览器缓存或点击"恢复默认"。</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
