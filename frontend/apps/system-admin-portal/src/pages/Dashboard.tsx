import React, { useState, useEffect } from 'react';
import { Building2, Users, Server, AlertCircle, TrendingUp, RefreshCw } from 'lucide-react';
import { api } from '../api/client';
import type { AnalyticsStats } from '../auth/types';
import { Loader2 } from 'lucide-react';

export default function Dashboard() {
  const [stats, setStats] = useState<AnalyticsStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadStats = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await api.getAnalytics();
      if (result.error) throw new Error(result.error);
      if (result.data) {
        setStats(result.data);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load stats');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadStats();
  }, []);

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
        <button onClick={loadStats} className="mt-4 text-emerald-600 hover:text-emerald-700">
          重试
        </button>
      </div>
    );
  }

  const statCards = [
    {
      title: '总租户数',
      value: stats?.activeTenants || 0,
      icon: Building2,
      color: 'bg-blue-500',
    },
    {
      title: '总用户数',
      value: stats?.totalUsers || 0,
      icon: Users,
      color: 'bg-purple-500',
    },
    {
      title: '总会话数',
      value: stats?.totalSessions || 0,
      icon: Server,
      color: 'bg-emerald-500',
    },
    {
      title: '总消息数',
      value: stats?.totalMessages || 0,
      icon: TrendingUp,
      color: 'bg-orange-500',
    },
  ];

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">系统概览</h3>
          <p className="text-gray-500">实时监控系统运行状态</p>
        </div>
        <button
          onClick={loadStats}
          className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
        >
          <RefreshCw className="w-4 h-4" />
          刷新
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {statCards.map((stat) => {
          const Icon = stat.icon;
          return (
            <div key={stat.title} className="card p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">{stat.title}</p>
                  <p className="text-2xl font-bold text-gray-900 mt-1">
                    {stat.value.toLocaleString()}
                  </p>
                </div>
                <div className={`w-12 h-12 ${stat.color} rounded-xl flex items-center justify-center`}>
                  <Icon className="w-6 h-6 text-white" />
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card p-6">
          <h4 className="font-semibold text-gray-900 mb-4">系统健康状态</h4>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
              <div className="flex items-center gap-3">
                <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                <span className="text-gray-900">所有服务运行正常</span>
              </div>
              <span className="text-sm text-green-700">健康</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-3">
                <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
                <span className="text-gray-900">API Gateway</span>
              </div>
              <span className="text-sm text-yellow-700">响应稍慢</span>
            </div>
          </div>
        </div>

        <div className="card p-6">
          <h4 className="font-semibold text-gray-900 mb-4">最近告警</h4>
          <div className="space-y-3">
            <div className="flex items-center gap-3 p-3 bg-red-50 rounded-lg">
              <AlertCircle className="w-5 h-5 text-red-600" />
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-900">存储空间不足</p>
                <p className="text-xs text-gray-500">10分钟前</p>
              </div>
            </div>
            <div className="flex items-center gap-3 p-3 bg-yellow-50 rounded-lg">
              <AlertCircle className="w-5 h-5 text-yellow-600" />
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-900">服务响应超时</p>
                <p className="text-xs text-gray-500">30分钟前</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}