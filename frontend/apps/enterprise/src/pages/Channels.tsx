import { useState } from 'react';
import { Card, CardContent, Button, Tag } from '@rag/ui';
import { Globe, MessageSquare, Smartphone, Link2 } from 'lucide-react';

interface Channel {
  id: string;
  name: string;
  type: 'web' | 'wechat' | 'app' | 'custom';
  status: 'active' | 'inactive';
  conversations: number;
}

export default function Channels() {
  const [channels] = useState<Channel[]>([
    { id: '1', name: '官网客服', type: 'web', status: 'active', conversations: 156 },
    { id: '2', name: '微信公众号', type: 'wechat', status: 'active', conversations: 89 },
    { id: '3', name: 'APP客服', type: 'app', status: 'inactive', conversations: 45 },
  ]);

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'web': return <Globe className="w-5 h-5" />;
      case 'wechat': return <MessageSquare className="w-5 h-5" />;
      case 'app': return <Smartphone className="w-5 h-5" />;
      default: return <Link2 className="w-5 h-5" />;
    }
  };

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">渠道接入</h2>
          <p className="text-gray-500">管理多渠道客服接入</p>
        </div>
        <Button leftIcon={<Link2 className="w-4 h-4" />}>
          添加渠道
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {channels.map((channel) => (
          <Card key={channel.id}>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center">
                    {getTypeIcon(channel.type)}
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">{channel.name}</p>
                    <p className="text-sm text-gray-500">{channel.conversations} 次对话</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <Tag variant={channel.status === 'active' ? 'success' : 'default'}>
                    {channel.status === 'active' ? '已启用' : '已禁用'}
                  </Tag>
                  <Button variant="secondary" size="sm">
                    配置
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
