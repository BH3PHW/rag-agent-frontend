import { useEffect } from 'react'
import { 
  MessageSquare, 
  Users, 
  Clock, 
  TrendingUp, 
  Activity,
  CheckCircle2,
  AlertCircle
} from 'lucide-react'
import { useAppStore } from '../store'
import { format } from 'date-fns'

export default function Dashboard() {
  const { stats, loadDashboard, waitingChats, myActiveChats, loadWaitingChats, loadMyActiveChats } = useAppStore()

  useEffect(() => {
    loadDashboard()
    loadWaitingChats()
    loadMyActiveChats()
  }, [])

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">仪表盘</h1>
          <p className="text-gray-600 mt-1">{format(new Date(), 'yyyy年MM月dd日')}</p>
        </div>
      </div>

      {/* 统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">当前会话</p>
              <p className="text-3xl font-bold text-blue-600 mt-2">
                {stats?.active_sessions || 0}
              </p>
            </div>
            <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center">
              <MessageSquare className="h-6 w-6 text-blue-600" />
            </div>
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">等待接入</p>
              <p className="text-3xl font-bold text-orange-600 mt-2">
                {stats?.waiting_sessions || 0}
              </p>
            </div>
            <div className="w-12 h-12 bg-orange-100 rounded-xl flex items-center justify-center">
              <AlertCircle className="h-6 w-6 text-orange-600" />
            </div>
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">今日处理</p>
              <p className="text-3xl font-bold text-green-600 mt-2">
                {stats?.total_chats_today || 0}
              </p>
            </div>
            <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center">
              <CheckCircle2 className="h-6 w-6 text-green-600" />
            </div>
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">在线坐席</p>
              <p className="text-3xl font-bold text-purple-600 mt-2">
                {stats?.online_agents || 0} / {stats?.total_agents || 0}
              </p>
            </div>
            <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center">
              <Users className="h-6 w-6 text-purple-600" />
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 等待接入的会话 */}
        <div className="card">
          <div className="p-6 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <AlertCircle className="h-5 w-5 text-orange-500" />
              等待接入的会话
            </h2>
          </div>
          <div className="p-6">
            {waitingChats.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <Activity className="h-12 w-12 mx-auto mb-3 text-gray-300" />
                <p>暂无等待中的会话</p>
              </div>
            ) : (
              <div className="space-y-3">
                {waitingChats.map((session) => (
                  <div key={session.id} className="flex items-center justify-between p-4 bg-orange-50 rounded-lg border border-orange-200">
                    <div>
                      <p className="font-medium text-gray-900">
                        {session.user_name || '未知用户'}
                      </p>
                      {session.topic && (
                        <p className="text-sm text-gray-500">{session.topic}</p>
                      )}
                      <p className="text-sm text-gray-500">
                        {format(new Date(session.started_at), 'HH:mm')}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      {session.priority > 0 && (
                        <span className="px-2 py-1 bg-red-100 text-red-700 rounded-full text-xs font-medium">
                          优先级 {session.priority}
                        </span>
                      )}
                      <span className="px-3 py-1 bg-orange-100 text-orange-700 rounded-full text-sm font-medium">
                        等待
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* 我的会话 */}
        <div className="card">
          <div className="p-6 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <Users className="h-5 w-5 text-blue-500" />
              我的会话
            </h2>
          </div>
          <div className="p-6">
            {myActiveChats.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <MessageSquare className="h-12 w-12 mx-auto mb-3 text-gray-300" />
                <p>暂无进行中的会话</p>
              </div>
            ) : (
              <div className="space-y-3">
                {myActiveChats.map((session) => (
                  <div key={session.id} className="flex items-center justify-between p-4 bg-blue-50 rounded-lg border border-blue-200">
                    <div>
                      <p className="font-medium text-gray-900">
                        {session.user_name || '未知用户'}
                      </p>
                      {session.topic && (
                        <p className="text-sm text-gray-500">{session.topic}</p>
                      )}
                    </div>
                    <span className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm font-medium">
                      进行中
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
