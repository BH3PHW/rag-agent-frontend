import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { 
  Home, 
  MessageSquare, 
  AlertCircle, 
  User, 
  LogOut,
  Settings
} from 'lucide-react'
import { useAppStore } from '../store'
import { useEffect } from 'react'

export default function Layout() {
  const navigate = useNavigate()
  const location = useLocation()
  const { agent, logout, updateAgentStatus } = useAppStore()

  useEffect(() => {
    if (!agent && location.pathname !== '/login') {
      navigate('/login')
    }
  }, [agent, location.pathname])

  const navItems = [
    { path: '/dashboard', icon: Home, label: '仪表盘' },
    { path: '/waiting', icon: AlertCircle, label: '等待接入' },
    { path: '/chats', icon: MessageSquare, label: '我的会话' },
  ]

  if (!agent) {
    return <Outlet />
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="flex h-screen">
        {/* 侧边栏 */}
        <aside className="w-64 bg-white border-r border-gray-200 flex flex-col">
          <div className="p-6 border-b border-gray-200">
            <h1 className="text-xl font-bold text-gray-900 flex items-center gap-2">
              <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                <User className="h-5 w-5 text-white" />
              </div>
              客服坐席
            </h1>
          </div>

          <nav className="flex-1 p-4 space-y-2">
            {navItems.map((item) => (
              <button
                key={item.path}
                onClick={() => navigate(item.path)}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                  location.pathname === item.path
                    ? 'bg-blue-50 text-blue-700'
                    : 'text-gray-600 hover:bg-gray-50'
                }`}
              >
                <item.icon className="h-5 w-5" />
                <span className="font-medium">{item.label}</span>
              </button>
            ))}
          </nav>

          <div className="p-4 border-t border-gray-200">
            <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg mb-4">
              <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                <User className="h-5 w-5 text-blue-600" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-medium text-gray-900 truncate">
                  {agent.username}
                </p>
                <p className="text-sm text-gray-500">坐席</p>
              </div>
            </div>

            <div className="space-y-2">
              <select
                value={agent.status || 'online'}
                onChange={(e) => updateAgentStatus(e.target.value as any)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
              >
                <option value="online">在线</option>
                <option value="busy">忙碌</option>
                <option value="offline">离线</option>
              </select>

              <button
                onClick={logout}
                className="w-full flex items-center gap-2 px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <LogOut className="h-4 w-4" />
                退出登录
              </button>
            </div>
          </div>
        </aside>

        {/* 主内容区 */}
        <main className="flex-1 overflow-auto">
          <div className="p-8">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  )
}
