import { useEffect, useState, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, Send, User, XCircle, CheckCircle2, Clock, Tag } from 'lucide-react'
import { useAppStore } from '../store'
import { format } from 'date-fns'

export default function ChatDetail() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const navigate = useNavigate()
  const { currentSession, loadSession, sendMessage, closeChat } = useAppStore()
  const [messageInput, setMessageInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (sessionId) {
      loadSession(sessionId)
    }
  }, [sessionId])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [currentSession?.messages])

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault()
    if (messageInput.trim() && sessionId) {
      sendMessage(sessionId, messageInput.trim())
      setMessageInput('')
    }
  }

  const handleCloseChat = () => {
    if (sessionId && confirm('确定要结束这个会话吗？')) {
      closeChat(sessionId)
      navigate('/chats')
    }
  }

  if (!currentSession) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-500">加载中...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-[calc(100vh-120px)]">
      {/* 顶部栏 */}
      <div className="card p-4 mb-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/chats')}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <ArrowLeft className="h-5 w-5 text-gray-600" />
          </button>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
              <User className="h-5 w-5 text-blue-600" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-semibold text-gray-900">
                  {currentSession.user_name || '未知用户'}
                </h3>
                {currentSession.priority > 0 && (
                  <span className="px-2 py-1 bg-red-100 text-red-700 rounded-full text-xs font-medium flex items-center gap-1">
                    <Tag className="h-3 w-3" />
                    优先级 {currentSession.priority}
                  </span>
                )}
              </div>
              <p className="text-sm text-gray-500">
                {currentSession.topic || '会话 ID: ' + currentSession.id.slice(0, 8) + '...'}
              </p>
            </div>
          </div>
        </div>
        <button
          onClick={handleCloseChat}
          className="btn btn-secondary flex items-center gap-2 text-red-600 hover:bg-red-50"
        >
          <XCircle className="h-4 w-4" />
          结束会话
        </button>
      </div>

      {/* 聊天区域 */}
      <div className="flex-1 card overflow-hidden flex flex-col">
        {/* 消息列表 */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {currentSession.messages.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <p>暂无消息</p>
            </div>
          ) : (
            currentSession.messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.sender_type === 'agent' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[70%] p-4 rounded-2xl ${
                    message.sender_type === 'agent'
                      ? 'bg-blue-600 text-white rounded-tr-md'
                      : 'bg-gray-100 text-gray-900 rounded-tl-md'
                  }`}
                >
                  <p className="whitespace-pre-wrap">{message.content}</p>
                  <p className={`text-xs mt-2 ${
                    message.sender_type === 'agent' ? 'text-blue-200' : 'text-gray-400'
                  }`}>
                    {format(new Date(message.created_at), 'HH:mm')}
                  </p>
                </div>
              </div>
            ))
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* 输入区域 */}
        <div className="border-t border-gray-200 p-4">
          <form onSubmit={handleSendMessage} className="flex gap-3">
            <input
              type="text"
              value={messageInput}
              onChange={(e) => setMessageInput(e.target.value)}
              placeholder="输入消息..."
              className="flex-1 px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
              autoFocus
            />
            <button
              type="submit"
              disabled={!messageInput.trim()}
              className="btn btn-primary px-6 flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Send className="h-4 w-4" />
              发送
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
