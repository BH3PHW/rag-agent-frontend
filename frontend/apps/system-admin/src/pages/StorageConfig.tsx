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
import { Database, HardDrive, Cloud, Server } from 'lucide-react';

interface StorageConfig {
  id: string;
  name: string;
  type: 'postgresql' | 'redis' | 'chroma' | 'minio';
  status: 'healthy' | 'warning' | 'error';
  usage: string;
  capacity: string;
}

export default function StorageConfigPage() {
  const [configs] = useState<StorageConfig[]>([
    { id: '1', name: 'PostgreSQL', type: 'postgresql', status: 'healthy', usage: '45%', capacity: '100GB' },
    { id: '2', name: 'Redis', type: 'redis', status: 'healthy', usage: '23%', capacity: '10GB' },
    { id: '3', name: 'ChromaDB', type: 'chroma', status: 'healthy', usage: '67%', capacity: '50GB' },
    { id: '4', name: 'MinIO', type: 'minio', status: 'warning', usage: '89%', capacity: '500GB' },
  ]);

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'postgresql': return <Database className="w-6 h-6 text-blue-600" />;
      case 'redis': return <Server className="w-6 h-6 text-red-600" />;
      case 'chroma': return <Cloud className="w-6 h-6 text-purple-600" />;
      case 'minio': return <HardDrive className="w-6 h-6 text-amber-600" />;
      default: return <HardDrive className="w-6 h-6 text-gray-600" />;
    }
  };

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">存储配置</h2>
          <p className="text-gray-500">管理数据库和存储服务配置</p>
        </div>
        <Button>
          添加存储
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {configs.map((config) => (
          <Card key={config.id}>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 bg-gray-100 rounded-xl flex items-center justify-center">
                    {getTypeIcon(config.type)}
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">{config.name}</h3>
                    <p className="text-sm text-gray-500">类型: {config.type}</p>
                  </div>
                </div>
                <Tag variant={config.status === 'healthy' ? 'success' : config.status === 'warning' ? 'warning' : 'danger'}>
                  {config.status === 'healthy' ? '健康' : config.status === 'warning' ? '警告' : '错误'}
                </Tag>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between text-sm mb-2">
                    <span className="text-gray-500">使用率</span>
                    <span className="font-medium">{config.usage} / {config.capacity}</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full ${
                        config.status === 'error' ? 'bg-red-500' :
                        config.status === 'warning' ? 'bg-amber-500' : 'bg-blue-500'
                      }`}
                      style={{ width: config.usage }}
                    />
                  </div>
                </div>
                <Input label="连接地址" defaultValue="localhost:5432" />
                <Input label="数据库名称" defaultValue="rag_service" />
              </div>
            </CardContent>
            <CardFooter>
              <div className="flex justify-end">
                <Button variant="secondary" size="sm">
                  测试连接
                </Button>
              </div>
            </CardFooter>
          </Card>
        ))}
      </div>
    </div>
  );
}
