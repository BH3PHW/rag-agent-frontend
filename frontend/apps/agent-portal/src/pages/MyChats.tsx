import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { MessageSquare, Users, Clock } from 'lucide-react'
import { useAppStore } from '../store'
import { format } from 'date-fns'

export default function MyChats() {
  const navigate = useNavigate()
  const { myActiveChats, loadMyActiveChats } = useAppStore()

  useEffect(() => {
    loadMyActiveChats()
    const interval = setInterval(loadMyActiveChats, 5000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">我的会话</h1>
          <p className="text-gray-600 mt-1">
            {myActiveChats.length} 个进行中的会话
          </p>
        </div>
      </div>

      {myActiveChats.length === 0 ? (
        <div className="card p-12 text-center">
          <MessageSquare className="h-16 w-16 mx-auto mb-4 text-gray-300" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">暂无进行中的会话</h3>
          <p className="text-gray-500">从等待接入列表接入会话开始</p>
        </div>
      ) : (
        <div className="space-y-4">
          {myActiveChats.map((session) => (
            <div
              key={session.id}
              className="card p-6 cursor-pointer hover:shadow-md transition-shadow"
              onClick={() => navigate(`/chats/${session.id}`)}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-4">
                  <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
                    <Users className="h-6 w-6 text-blue-600" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="text-lg font-semibold text-gray-900">
                        {session.user_name || '未知用户'}
                      </h3>
                      <span className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm font-medium">
                        进行中
                      </span>
                    </div>
                    <div className="flex items-center gap-4 text-sm text-gray-500 mb-3">
                      <span className="flex items-center gap-1">
                        <Clock className="h-4 w-4" />
                        {format(new Date(session.started_at), 'yyyy-MM-dd HH:mm')}
                      </span>
                      {session.topic && (
                        <span className="text-gray-600">{session.topic}</span>
                      )}
                    </div>
                  </div>
                </div>
                <div className="text-gray-400">
                  <MessageSquare className="h-6 w-6" />
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
