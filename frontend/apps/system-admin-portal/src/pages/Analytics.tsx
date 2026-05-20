import React, { useState, useEffect } from 'react';
import { BarChart3, TrendingUp, Users, MessageSquare, FileText, RefreshCw } from 'lucide-react';
import { api } from '../api/client';
import type { AnalyticsStats } from '../auth/types';
import { Loader2 } from 'lucide-react';

export default function Analytics() {
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
      setError(err instanceof Error ? err.message : 'Failed to load analytics');
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
    { title: '总会话数', value: stats?.totalSessions || 0, icon: MessageSquare, color: 'bg-blue-500' },
    { title: '总消息数', value: stats?.totalMessages || 0, icon: TrendingUp, color: 'bg-purple-500' },
    { title: '总用户数', value: stats?.totalUsers || 0, icon: Users, color: 'bg-emerald-500' },
    { title: '总文档数', value: stats?.totalDocuments || 0, icon: FileText, color: 'bg-orange-500' },
  ];

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">数据分析</h3>
          <p className="text-gray-500">系统运行数据统计和分析</p>
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

      <div className="card p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <h4 className="font-semibold text-gray-900">数据趋势</h4>
        </div>
        <div className="h-64 flex items-center justify-center text-gray-400">
          <BarChart3 className="w-12 h-12 mr-4" />
          <p>图表展示区域（需要集成图表库）</p>
        </div>
      </div>
    </div>
  );
}