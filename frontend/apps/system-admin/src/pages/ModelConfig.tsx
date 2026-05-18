import { useState } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  CardFooter,
  Button,
  Input,
  Tag
} from '@rag/ui';
import { Bot, Key, CheckCircle2, AlertCircle } from 'lucide-react';

interface ModelProvider {
  id: string;
  name: string;
  type: 'openai' | 'anthropic' | 'azure' | 'ollama';
  status: 'connected' | 'disconnected' | 'error';
  models: string[];
}

export default function ModelConfig() {
  const [providers] = useState<ModelProvider[]>([
    { id: '1', name: 'OpenAI', type: 'openai', status: 'connected', models: ['gpt-4', 'gpt-3.5-turbo'] },
    { id: '2', name: 'Claude', type: 'anthropic', status: 'connected', models: ['claude-3-opus', 'claude-3-sonnet'] },
    { id: '3', name: 'Azure OpenAI', type: 'azure', status: 'disconnected', models: [] },
    { id: '4', name: 'Ollama (本地)', type: 'ollama', status: 'error', models: ['llama2', 'mistral'] },
  ]);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'connected': return <CheckCircle2 className="w-4 h-4 text-green-500" />;
      case 'disconnected': return <AlertCircle className="w-4 h-4 text-gray-400" />;
      case 'error': return <AlertCircle className="w-4 h-4 text-red-500" />;
      default: return null;
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'connected': return '已连接';
      case 'disconnected': return '未连接';
      case 'error': return '错误';
      default: return '未知';
    }
  };

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">大模型配置</h2>
          <p className="text-gray-500">配置AI大模型提供商和API密钥</p>
        </div>
        <Button leftIcon={<Key className="w-4 h-4" />}>
          添加提供商
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {providers.map((provider) => (
          <Card key={provider.id}>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center">
                    <Bot className="w-6 h-6 text-purple-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">{provider.name}</h3>
                    <p className="text-sm text-gray-500">类型: {provider.type}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {getStatusIcon(provider.status)}
                  <span className="text-sm text-gray-600">{getStatusText(provider.status)}</span>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {provider.status === 'connected' && provider.models.length > 0 ? (
                <div>
                  <p className="text-sm text-gray-500 mb-3">可用模型:</p>
                  <div className="flex flex-wrap gap-2">
                    {provider.models.map((model) => (
                      <Tag key={model}>{model}</Tag>
                    ))}
                  </div>
                </div>
              ) : provider.status === 'disconnected' ? (
                <div className="space-y-4">
                  <Input label="API Key" type="password" placeholder="sk-..." />
                  <Input label="API Endpoint" placeholder="https://api.openai.com/v1" />
                </div>
              ) : (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <p className="text-sm text-red-600">连接失败，请检查配置和网络</p>
                </div>
              )}
            </CardContent>
            <CardFooter>
              <div className="flex justify-end gap-2">
                <Button variant="secondary" size="sm">
                  测试连接
                </Button>
                <Button size="sm">
                  {provider.status === 'connected' ? '保存' : '连接'}
                </Button>
              </div>
            </CardFooter>
          </Card>
        ))}
      </div>
    </div>
  );
}
