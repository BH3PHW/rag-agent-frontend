import { useState } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  Button,
  Tag
} from '@rag/ui';
import {
  Bell,
  AlertTriangle,
  Info,
  Trash2
} from 'lucide-react';

interface Alert {
  id: string;
  type: 'error' | 'warning' | 'info';
  title: string;
  message: string;
  service: string;
  time: string;
  status: 'unread' | 'read';
}

export default function Alerts() {
  const [alerts] = useState<Alert[]>([
    { id: '1', type: 'error', title: '服务连接失败', message: 'Analytics Service 无法连接到数据库', service: 'Analytics Service', time: '10分钟前', status: 'unread' },
    { id: '2', type: 'warning', title: '存储空间不足', message: 'MinIO 存储使用率超过 85%', service: 'Storage', time: '30分钟前', status: 'unread' },
    { id: '3', type: 'warning', title: 'API 限流', message: 'API Gateway 检测到异常请求频率', service: 'API Gateway', time: '1小时前', status: 'unread' },
    { id: '4', type: 'info', title: '服务重启', message: 'Channel Service 已成功重启', service: 'Channel Service', time: '2小时前', status: 'read' },
    { id: '5', type: 'error', title: '认证失败', message: '检测到异常的登录尝试', service: 'User Service', time: '3小时前', status: 'read' },
  ]);

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'error': return <AlertTriangle className="w-5 h-5 text-red-500" />;
      case 'warning': return <AlertTriangle className="w-5 h-5 text-amber-500" />;
      case 'info': return <Info className="w-5 h-5 text-blue-500" />;
      default: return <Info className="w-5 h-5 text-gray-500" />;
    }
  };

  const getTypeTag = (type: string) => {
    switch (type) {
      case 'error': return <Tag variant="danger">错误</Tag>;
      case 'warning': return <Tag variant="warning">警告</Tag>;
      case 'info': return <Tag>通知</Tag>;
      default: return <Tag>未知</Tag>;
    }
  };

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">告警中心</h2>
          <p className="text-gray-500">系统告警和异常通知</p>
        </div>
        <Button variant="secondary">
          全部已读
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 mb-8">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">未读告警</p>
                <p className="text-2xl font-bold text-red-600">
                  {alerts.filter(a => a.status === 'unread').length}
                </p>
              </div>
              <div className="w-12 h-12 bg-red-100 rounded-xl flex items-center justify-center">
                <Bell className="w-6 h-6 text-red-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">错误告警</p>
                <p className="text-2xl font-bold text-gray-900">
                  {alerts.filter(a => a.type === 'error').length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">警告告警</p>
                <p className="text-2xl font-bold text-amber-600">
                  {alerts.filter(a => a.type === 'warning').length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">今日告警</p>
                <p className="text-2xl font-bold text-gray-900">12</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <h3 className="font-semibold text-gray-900">告警列表</h3>
        </CardHeader>
        <CardContent className="divide-y divide-gray-100">
          {alerts.map((alert) => (
            <div key={alert.id} className="py-4 flex items-start justify-between">
              <div className="flex items-start gap-4">
                <div className="mt-1">
                  {getTypeIcon(alert.type)}
                </div>
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <p className="font-medium text-gray-900">{alert.title}</p>
                    {getTypeTag(alert.type)}
                    {alert.status === 'unread' && (
                      <div className="w-2 h-2 bg-red-500 rounded-full" />
                    )}
                  </div>
                  <p className="text-sm text-gray-600 mb-1">{alert.message}</p>
                  <p className="text-xs text-gray-400">
                    {alert.service} · {alert.time}
                  </p>
                </div>
              </div>
              <Button variant="secondary" size="sm" leftIcon={<Trash2 className="w-4 h-4" />}>
                删除
              </Button>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
