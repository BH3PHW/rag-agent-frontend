import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { AlertCircle, Clock, User, PhoneIncoming, Tag } from 'lucide-react'
import { useAppStore } from '../store'
import { format } from 'date-fns'

export default function WaitingChats() {
  const navigate = useNavigate()
  const { waitingChats, loadWaitingChats, acceptChat } = useAppStore()

  useEffect(() => {
    loadWaitingChats()
    const interval = setInterval(loadWaitingChats, 10000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">等待接入</h1>
          <p className="text-gray-600 mt-1">
            {waitingChats.length} 个会话等待接入
          </p>
        </div>
      </div>

      {waitingChats.length === 0 ? (
        <div className="card p-12 text-center">
          <AlertCircle className="h-16 w-16 mx-auto mb-4 text-gray-300" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">暂无等待中的会话</h3>
          <p className="text-gray-500">当有新的会话需要人工介入时，会显示在这里</p>
        </div>
      ) : (
        <div className="space-y-4">
          {waitingChats.map((session) => (
            <div key={session.id} className="card p-6">
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-4">
                  <div className="w-12 h-12 bg-orange-100 rounded-full flex items-center justify-center flex-shrink-0">
                    <User className="h-6 w-6 text-orange-600" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3 mb-2 flex-wrap">
                      <h3 className="text-lg font-semibold text-gray-900">
                        {session.user_name || '未知用户'}
                      </h3>
                      {session.priority > 0 && (
                        <span className="px-2 py-1 bg-red-100 text-red-700 rounded-full text-xs font-medium flex items-center gap-1">
                          <Tag className="h-3 w-3" />
                          优先级 {session.priority}
                        </span>
                      )}
                      <span className="px-3 py-1 bg-orange-100 text-orange-700 rounded-full text-sm font-medium">
                        等待接入
                      </span>
                    </div>
                    <div className="flex items-center gap-4 text-sm text-gray-500 mb-3">
                      <span className="flex items-center gap-1">
                        <Clock className="h-4 w-4" />
                        {format(new Date(session.started_at), 'HH:mm:ss')}
                      </span>
                      {session.topic && (
                        <span className="text-gray-600">{session.topic}</span>
                      )}
                    </div>
                  </div>
                </div>
                <button
                  onClick={() => acceptChat(session.session_id)}
                  className="btn btn-primary flex items-center gap-2"
                >
                  <PhoneIncoming className="h-4 w-4" />
                  接入会话
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
