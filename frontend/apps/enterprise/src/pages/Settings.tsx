import { useState } from 'react';
import { Card, CardContent, CardHeader, Input, Textarea, Button } from '@rag/ui';
import { Settings, Bot, Shield, Database } from 'lucide-react';

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState('general');

  return (
    <div className="p-8">
      <div className="mb-8">
        <h2 className="text-lg font-semibold text-gray-900">系统设置</h2>
        <p className="text-gray-500">配置企业客服系统参数</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <Card className="lg:col-span-1">
          <CardContent className="p-4">
            <nav className="space-y-1">
              {[
                { id: 'general', label: '基本设置', icon: Settings },
                { id: 'ai', label: 'AI设置', icon: Bot },
                { id: 'security', label: '安全设置', icon: Shield },
                { id: 'storage', label: '存储设置', icon: Database },
              ].map((item) => (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors text-left ${
                    activeTab === item.id
                      ? 'bg-blue-50 text-blue-700 font-medium'
                      : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                  }`}
                >
                  <item.icon className="w-5 h-5" />
                  <span>{item.label}</span>
                </button>
              ))}
            </nav>
          </CardContent>
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader>
            <h3 className="font-semibold text-gray-900">基本设置</h3>
          </CardHeader>
          <CardContent className="space-y-6">
            <Input label="企业名称" placeholder="请输入企业名称" />
            <Input label="客服名称" placeholder="请输入客服显示名称" />
            <Textarea label="欢迎语" placeholder="用户进入时的欢迎语" />
            <div className="flex justify-end">
              <Button>保存设置</Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
