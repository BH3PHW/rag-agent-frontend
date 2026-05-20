import React, { useState, useEffect } from 'react';
import { Building2, Plus, Search, RefreshCw, Edit2, Trash2 } from 'lucide-react';
import { api } from '../api/client';
import type { Enterprise } from '../auth/types';
import { Loader2 } from 'lucide-react';

export default function Tenants() {
  const [tenants, setTenants] = useState<Enterprise[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  const loadTenants = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await api.getEnterprises();
      if (result.error) throw new Error(result.error);
      if (result.data) {
        setTenants(result.data.enterprises || []);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load tenants');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadTenants();
  }, []);

  const filteredTenants = tenants.filter(tenant =>
    tenant.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const getStatusTag = (status: string) => {
    return status === 'active' 
      ? <span className="px-2 py-1 bg-green-100 text-green-700 text-xs rounded-full">活跃</span>
      : <span className="px-2 py-1 bg-red-100 text-red-700 text-xs rounded-full">已暂停</span>;
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="w-8 h-8 animate-spin text-emerald-600" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <p className="text-red-700">{error}</p>
        <button onClick={loadTenants} className="mt-4 text-emerald-600 hover:text-emerald-700">
          重试
        </button>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">租户管理</h3>
          <p className="text-gray-500">管理系统中的所有租户（企业客户）</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={loadTenants}
            className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            <RefreshCw className="w-4 h-4" />
            刷新
          </button>
          <button className="flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700">
            <Plus className="w-4 h-4" />
            创建租户
          </button>
        </div>
      </div>

      <div className="mb-6">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            placeholder="搜索租户..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
          />
        </div>
      </div>

      <div className="card overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">租户</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">用户数</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">文档数</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">会话数</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">状态</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">操作</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {filteredTenants.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-6 py-8 text-center text-gray-500">
                  没有找到租户
                </td>
              </tr>
            ) : (
              filteredTenants.map((tenant) => (
                <tr key={tenant.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                        <Building2 className="w-5 h-5 text-blue-600" />
                      </div>
                      <div>
                        <p className="font-medium text-gray-900">{tenant.name}</p>
                        <p className="text-xs text-gray-500">ID: {tenant.id}</p>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-gray-900">{tenant.userCount}</td>
                  <td className="px-6 py-4 text-gray-900">{tenant.documentCount}</td>
                  <td className="px-6 py-4 text-gray-900">{tenant.sessionCount}</td>
                  <td className="px-6 py-4">{getStatusTag(tenant.status)}</td>
                  <td className="px-6 py-4 text-right">
                    <div className="flex justify-end gap-2">
                      <button className="p-2 text-gray-400 hover:text-gray-600">
                        <Edit2 className="w-4 h-4" />
                      </button>
                      <button className="p-2 text-red-400 hover:text-red-600">
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}