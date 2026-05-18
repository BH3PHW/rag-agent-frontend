import { useState } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  Button,
  Input,
  Tag
} from '@rag/ui';
import { Building2, Plus, Users, Edit2 } from 'lucide-react';

interface Tenant {
  id: string;
  name: string;
  plan: 'free' | 'basic' | 'pro' | 'enterprise';
  users: number;
  status: 'active' | 'suspended';
  createdAt: string;
}

export default function Tenants() {
  const [tenants] = useState<Tenant[]>([
    { id: '1', name: '科技有限公司', plan: 'enterprise', users: 150, status: 'active', createdAt: '2024-01-01' },
    { id: '2', name: '电子商务公司', plan: 'pro', users: 45, status: 'active', createdAt: '2024-01-15' },
    { id: '3', name: '教育培训中心', plan: 'basic', users: 12, status: 'active', createdAt: '2024-02-01' },
    { id: '4', name: '个人测试账户', plan: 'free', users: 1, status: 'suspended', createdAt: '2024-02-15' },
  ]);

  const getPlanTag = (plan: string) => {
    switch (plan) {
      case 'enterprise': return <Tag variant="success">企业版</Tag>;
      case 'pro': return <Tag variant="warning">专业版</Tag>;
      case 'basic': return <Tag>基础版</Tag>;
      case 'free': return <Tag>免费版</Tag>;
      default: return <Tag>未知</Tag>;
    }
  };

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">租户管理</h2>
          <p className="text-gray-500">管理系统中的所有租户（企业客户）</p>
        </div>
        <Button leftIcon={<Plus className="w-4 h-4" />}>
          创建租户
        </Button>
      </div>

      <div className="mb-6">
        <Input
          placeholder="搜索租户..."
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 mb-8">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">总租户数</p>
                <p className="text-2xl font-bold text-gray-900">156</p>
              </div>
              <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center">
                <Building2 className="w-6 h-6 text-blue-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">活跃租户</p>
                <p className="text-2xl font-bold text-green-600">142</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">总用户数</p>
                <p className="text-2xl font-bold text-gray-900">2,458</p>
              </div>
              <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center">
                <Users className="w-6 h-6 text-purple-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">本月新增</p>
                <p className="text-2xl font-bold text-gray-900">23</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <h3 className="font-semibold text-gray-900">租户列表</h3>
        </CardHeader>
        <CardContent className="divide-y divide-gray-100">
          {tenants.map((tenant) => (
            <div key={tenant.id} className="py-4 flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center">
                  <Building2 className="w-6 h-6 text-blue-600" />
                </div>
                <div>
                  <p className="font-medium text-gray-900">{tenant.name}</p>
                  <p className="text-sm text-gray-500">
                    {tenant.users} 用户 · 创建于 {tenant.createdAt}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                {getPlanTag(tenant.plan)}
                <Tag variant={tenant.status === 'active' ? 'success' : 'danger'}>
                  {tenant.status === 'active' ? '活跃' : '已暂停'}
                </Tag>
                <Button variant="secondary" size="sm" leftIcon={<Edit2 className="w-4 h-4" />}>
                  编辑
                </Button>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
