import { useState } from 'react';
import { Card, CardContent, CardHeader, Button } from '@rag/ui';
import { Users, CheckCircle2, XCircle, Clock } from 'lucide-react';

interface Agent {
  id: string;
  name: string;
  status: 'online' | 'offline' | 'busy';
  currentChats: number;
  totalChats: number;
}

export default function HumanAgent() {
  const [agents] = useState<Agent[]>([
    { id: '1', name: '李小明', status: 'online', currentChats: 2, totalChats: 45 },
    { id: '2', name: '王小红', status: 'busy', currentChats: 4, totalChats: 38 },
    { id: '3', name: '张小强', status: 'offline', currentChats: 0, totalChats: 52 },
  ]);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'online': return <CheckCircle2 className="w-4 h-4 text-green-500" />;
      case 'busy': return <Clock className="w-4 h-4 text-amber-500" />;
      case 'offline': return <XCircle className="w-4 h-4 text-gray-400" />;
      default: return null;
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'online': return '在线';
      case 'busy': return '忙碌';
      case 'offline': return '离线';
      default: return '未知';
    }
  };

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">人工客服管理</h2>
          <p className="text-gray-500">管理人工客服团队和对话转接</p>
        </div>
        <Button leftIcon={<Users className="w-4 h-4" />}>
          添加客服
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">在线坐席</p>
                <p className="text-2xl font-bold text-green-600">5</p>
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
                <p className="text-sm text-gray-500">忙碌坐席</p>
                <p className="text-2xl font-bold text-amber-600">2</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">今日处理</p>
                <p className="text-2xl font-bold text-gray-900">32</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <h3 className="font-semibold text-gray-900">坐席列表</h3>
        </CardHeader>
        <CardContent className="divide-y divide-gray-100">
          {agents.map((agent) => (
            <div key={agent.id} className="py-4 flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                    <Users className="w-5 h-5 text-blue-600" />
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">{agent.name}</p>
                    <p className="text-sm text-gray-500">
                      正在处理 {agent.currentChats} 个对话 · 累计 {agent.totalChats} 个
                    </p>
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-2">
                  {getStatusIcon(agent.status)}
                  <span className="text-sm text-gray-600">{getStatusText(agent.status)}</span>
                </div>
                <Button variant="secondary" size="sm">
                  详情
                </Button>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
