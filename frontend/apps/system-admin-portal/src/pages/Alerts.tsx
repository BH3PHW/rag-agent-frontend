import React, { useState, useEffect } from 'react';
import { Bell, Check, X, RefreshCw, AlertTriangle, Info } from 'lucide-react';
import { api } from '../api/client';
import type { Alert } from '../auth/types';
import { Loader2 } from 'lucide-react';

export default function Alerts() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('');

  const loadAlerts = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await api.getAlerts(statusFilter || undefined);
      if (result.error) throw new Error(result.error);
      if (result.data) {
        setAlerts(result.data.alerts || []);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load alerts');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadAlerts();
  }, [statusFilter]);

  const handleAcknowledge = async (id: string) => {
    try {
      await api.acknowledgeAlert(id);
      loadAlerts();
    } catch (err) {
      console.error('Failed to acknowledge alert:', err);
    }
  };

  const handleResolve = async (id: string) => {
    try {
      await api.resolveAlert(id);
      loadAlerts();
    } catch (err) {
      console.error('Failed to resolve alert:', err);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('确定要删除这条告警吗？')) return;
    try {
      await api.deleteAlert(id);
      loadAlerts();
    } catch (err) {
      console.error('Failed to delete alert:', err);
    }
  };

  const getLevelIcon = (level: string) => {
    switch (level) {
      case 'critical':
        return <AlertTriangle className="w-5 h-5 text-red-600" />;
      case 'warning':
        return <AlertTriangle className="w-5 h-5 text-yellow-600" />;
      default:
        return <Info className="w-5 h-5 text-blue-600" />;
    }
  };

  const getLevelBg = (level: string) => {
    switch (level) {
      case 'critical':
        return 'bg-red-50 border-red-200';
      case 'warning':
        return 'bg-yellow-50 border-yellow-200';
      default:
        return 'bg-blue-50 border-blue-200';
    }
  };

  const getStatusTag = (status: string) => {
    switch (status) {
      case 'active':
        return <span className="px-2 py-1 bg-red-100 text-red-700 text-xs rounded-full">待处理</span>;
      case 'acknowledged':
        return <span className="px-2 py-1 bg-yellow-100 text-yellow-700 text-xs rounded-full">已确认</span>;
      case 'resolved':
        return <span className="px-2 py-1 bg-green-100 text-green-700 text-xs rounded-full">已解决</span>;
      default:
        return <span className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded-full">{status}</span>;
    }
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
        <button onClick={loadAlerts} className="mt-4 text-emerald-600 hover:text-emerald-700">
          重试
        </button>
      </div>
    );
  }

  const activeCount = alerts.filter(a => a.status === 'active').length;
  const acknowledgedCount = alerts.filter(a => a.status === 'acknowledged').length;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">告警中心</h3>
          <p className="text-gray-500">管理和处理系统告警</p>
        </div>
        <div className="flex gap-2">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
          >
            <option value="">所有状态</option>
            <option value="active">待处理</option>
            <option value="acknowledged">已确认</option>
            <option value="resolved">已解决</option>
          </select>
          <button
            onClick={loadAlerts}
            className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            <RefreshCw className="w-4 h-4" />
            刷新
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="card p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">待处理告警</p>
              <p className="text-2xl font-bold text-red-600">{activeCount}</p>
            </div>
            <div className="w-10 h-10 bg-red-100 rounded-lg flex items-center justify-center">
              <Bell className="w-5 h-5 text-red-600" />
            </div>
          </div>
        </div>
        <div className="card p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">已确认告警</p>
              <p className="text-2xl font-bold text-yellow-600">{acknowledgedCount}</p>
            </div>
            <div className="w-10 h-10 bg-yellow-100 rounded-lg flex items-center justify-center">
              <Bell className="w-5 h-5 text-yellow-600" />
            </div>
          </div>
        </div>
        <div className="card p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">总告警数</p>
              <p className="text-2xl font-bold text-gray-900">{alerts.length}</p>
            </div>
            <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
              <Bell className="w-5 h-5 text-blue-600" />
            </div>
          </div>
        </div>
      </div>

      <div className="space-y-4">
        {alerts.length === 0 ? (
          <div className="card p-8 text-center text-gray-500">
            没有告警信息
          </div>
        ) : (
          alerts.map((alert) => (
            <div
              key={alert.id}
              className={`card p-4 border-2 ${getLevelBg(alert.level)}`}
            >
              <div className="flex items-start gap-4">
                <div className="mt-1">
                  {getLevelIcon(alert.level)}
                </div>
                <div className="flex-1">
                  <div className="flex items-start justify-between">
                    <div>
                      <h4 className="font-medium text-gray-900">{alert.message}</h4>
                      <p className="text-sm text-gray-500 mt-1">
                        类型: {alert.type} · 级别: {alert.level} · {new Date(alert.createdAt).toLocaleString()}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      {getStatusTag(alert.status)}
                    </div>
                  </div>
                  {alert.status !== 'resolved' && (
                    <div className="flex gap-2 mt-4">
                      {alert.status === 'active' && (
                        <button
                          onClick={() => handleAcknowledge(alert.id)}
                          className="flex items-center gap-1 px-3 py-1 bg-yellow-100 text-yellow-700 rounded-lg hover:bg-yellow-200"
                        >
                          <Check className="w-4 h-4" />
                          确认
                        </button>
                      )}
                      <button
                        onClick={() => handleResolve(alert.id)}
                        className="flex items-center gap-1 px-3 py-1 bg-green-100 text-green-700 rounded-lg hover:bg-green-200"
                      >
                        <Check className="w-4 h-4" />
                        解决
                      </button>
                      <button
                        onClick={() => handleDelete(alert.id)}
                        className="flex items-center gap-1 px-3 py-1 bg-red-100 text-red-700 rounded-lg hover:bg-red-200"
                      >
                        <X className="w-4 h-4" />
                        删除
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}