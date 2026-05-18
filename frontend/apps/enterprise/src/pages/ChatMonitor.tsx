import { useState } from 'react';
import { Card, CardContent, Tag, Button } from '@rag/ui';
import { MessageSquare, User, Eye } from 'lucide-react';

interface ChatSession {
  id: string;
  user: string;
  lastMessage: string;
  messages: number;
  status: 'active' | 'waiting' | 'ended';
  startTime: string;
}

export default function ChatMonitor() {
  const [sessions] = useState<ChatSession[]>([
    { id: '1', user: '张三', lastMessage: '请问产品如何退货？', messages: 12, status: 'active', startTime: '10:23' },
    { id: '2', user: '李四', lastMessage: '发货时间是多久？', messages: 8, status: 'waiting', startTime: '10:18' },
    { id: '3', user: '王五', lastMessage: '谢谢，问题已解决', messages: 5, status: 'ended', startTime: '09:45' },
  ]);

  const getStatusTag = (status: string) => {
    switch (status) {
      case 'active': return <Tag variant="success">进行中</Tag>;
      case 'waiting': return <Tag variant="warning">等待中</Tag>;
      case 'ended': return <Tag>已结束</Tag>;
      default: return <Tag>未知</Tag>;
    }
  };

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">对话监控</h2>
          <p className="text-gray-500">实时查看用户对话情况</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 mb-8">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">活跃对话</p>
                <p className="text-2xl font-bold text-gray-900">5</p>
              </div>
              <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center">
                <MessageSquare className="w-6 h-6 text-green-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">今日对话</p>
                <p className="text-2xl font-bold text-gray-900">128</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">等待人工</p>
                <p className="text-2xl font-bold text-amber-600">3</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">满意度</p>
                <p className="text-2xl font-bold text-gray-900">96%</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {sessions.map((session) => (
          <Card key={session.id}>
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                    <User className="w-5 h-5 text-blue-600" />
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">{session.user}</p>
                    <p className="text-sm text-gray-500">{session.startTime} · {session.messages} 条消息</p>
                  </div>
                </div>
                {getStatusTag(session.status)}
              </div>
              <div className="bg-gray-50 rounded-lg p-4 mb-4">
                <p className="text-sm text-gray-600 line-clamp-2">{session.lastMessage}</p>
              </div>
              <div className="flex justify-end">
                <Button variant="secondary" size="sm" leftIcon={<Eye className="w-4 h-4" />}>
                  查看详情
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
