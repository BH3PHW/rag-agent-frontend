import { useState } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  Tag,
  Button
} from '@rag/ui';
import {
  Server,
  Cpu,
  MemoryStick,
  Wifi,
  RefreshCw,
  CheckCircle2
} from 'lucide-react';

interface Service {
  id: string;
  name: string;
  status: 'running' | 'stopped' | 'error';
  uptime: string;
  cpu: string;
  memory: string;
  requests: number;
}

export default function Services() {
  const [services] = useState<Service[]>([
    { id: '1', name: 'API Gateway', status: 'running', uptime: '15d 7h', cpu: '12%', memory: '256MB', requests: 1250 },
    { id: '2', name: 'User Service', status: 'running', uptime: '15d 7h', cpu: '8%', memory: '128MB', requests: 450 },
    { id: '3', name: 'Chat Service', status: 'running', uptime: '15d 7h', cpu: '45%', memory: '512MB', requests: 320 },
    { id: '4', name: 'Knowledge Service', status: 'running', uptime: '15d 7h', cpu: '23%', memory: '384MB', requests: 180 },
    { id: '5', name: 'Channel Service', status: 'stopped', uptime: '-', cpu: '0%', memory: '0MB', requests: 0 },
    { id: '6', name: 'Analytics Service', status: 'error', uptime: '2h', cpu: '5%', memory: '64MB', requests: 15 },
  ]);

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">服务监控</h2>
          <p className="text-gray-500">监控所有微服务的运行状态</p>
        </div>
        <Button leftIcon={<RefreshCw className="w-4 h-4" />}>
          刷新状态
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 mb-8">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">运行中</p>
                <p className="text-2xl font-bold text-green-600">
                  {services.filter(s => s.status === 'running').length}
                </p>
              </div>
              <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center">
                <CheckCircle2 className="w-6 h-6 text-green-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">已停止</p>
                <p className="text-2xl font-bold text-gray-600">
                  {services.filter(s => s.status === 'stopped').length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">错误</p>
                <p className="text-2xl font-bold text-red-600">
                  {services.filter(s => s.status === 'error').length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">总请求</p>
                <p className="text-2xl font-bold text-blue-600">2,265</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <h3 className="font-semibold text-gray-900">服务列表</h3>
        </CardHeader>
        <CardContent className="divide-y divide-gray-100">
          {services.map((service) => (
            <div key={service.id} className="py-4 flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center">
                  <Server className="w-6 h-6 text-blue-600" />
                </div>
                <div>
                  <p className="font-medium text-gray-900">{service.name}</p>
                  <p className="text-sm text-gray-500">运行时间: {service.uptime}</p>
                </div>
              </div>
              <div className="flex items-center gap-6">
                <div className="flex items-center gap-6 text-sm">
                  <div className="flex items-center gap-2">
                    <Cpu className="w-4 h-4 text-gray-400" />
                    <span>{service.cpu}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <MemoryStick className="w-4 h-4 text-gray-400" />
                    <span>{service.memory}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Wifi className="w-4 h-4 text-gray-400" />
                    <span>{service.requests}/min</span>
                  </div>
                </div>
                <Tag variant={service.status === 'running' ? 'success' : service.status === 'error' ? 'danger' : 'default'}>
                  {service.status === 'running' ? '运行中' : service.status === 'stopped' ? '已停止' : '错误'}
                </Tag>
                <Button variant="secondary" size="sm">
                  {service.status === 'running' ? '重启' : '启动'}
                </Button>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
